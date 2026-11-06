"""Silent local observations; never interprets liveness as remote-model progress.

Reads operational event counts only. No reasoning/code contents are persisted.
No inference calls, process termination, retry or budget decisions occur here.
"""
import codecs
from collections import Counter
import json
from pathlib import Path
import threading
import time


class ProgressMonitor:
    def __init__(self,stem,operation,timeout,heartbeat_seconds=600,tick_seconds=5,clock=time.monotonic):
        self.stem=Path(stem);self.operation=operation;self.timeout=timeout
        self.heartbeat_seconds=heartbeat_seconds;self.tick_seconds=tick_seconds;self.clock=clock
        self.started=clock();self.next_heartbeat=self.started+heartbeat_seconds
        self.offset=0;self.pending='';self.decoder=codecs.getincrementaldecoder('utf-8-sig')('replace')
        self.events=Counter();self.characters=Counter();self.last_output=None;self.session_ids=set()
        self.stop=threading.Event();self.thread=None;self.observer_error=None

    def _read_events(self,now):
        path=Path(str(self.stem)+'.stdout')
        if not path.exists():return
        with path.open('rb') as stream:
            stream.seek(self.offset);chunk=stream.read(8*1024*1024);self.offset+=len(chunk)
        self.pending+=self.decoder.decode(chunk)
        lines=self.pending.split('\n');self.pending=lines.pop()
        # An oversized/incomplete line is not a progress claim or instruction.
        if len(self.pending)>8*1024*1024:self.pending=''
        allowed={'step_start','step_finish','text','reasoning','thinking','reasoning_delta','error','tool_use'}
        for line in lines:
            if not line.strip():continue
            try:event=json.loads(line)
            except ValueError:continue
            if not isinstance(event,dict):continue
            kind=event.get('type');kind=kind if isinstance(kind,str) and kind in allowed else 'other'
            self.events[kind]+=1
            sid=event.get('sessionID')
            if isinstance(sid,str) and sid.startswith('ses_') and len(sid)<128:self.session_ids.add(sid)
            part=event.get('part',{});part=part if isinstance(part,dict) else {}
            text=part.get('text','');length=len(text) if isinstance(text,str) else 0
            self.characters[kind]+=length
            if kind in {'text','reasoning','thinking','reasoning_delta'} and length:self.last_output=now

    def snapshot(self,terminal=None):
        now=self.clock();self._read_events(now)
        elapsed=max(0,now-self.started)
        recent=self.last_output is not None and now-self.last_output<=60
        if terminal:status=terminal
        elif self.events['error']:status='error_event_observed'
        elif self.events['tool_use']:status='unexpected_tool_event_observed'
        elif self.operation!='model_request':status='local_operation_pending'
        elif recent:status='visible_model_output_recent'
        else:status='waiting_no_visible_model_progress'
        row=dict(updated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
            operation=self.operation,attempt_directory=self.stem.parent.name,
            elapsed_seconds=round(elapsed,3),request_limit_seconds=self.timeout,
            native_call_pending=terminal is None,status=status,
            event_counts=dict(self.events),content_character_counts=dict(self.characters),
            last_visible_model_output_age_seconds=round(now-self.last_output,3) if self.last_output is not None else None,
            session_ids=sorted(self.session_ids),observer_error=self.observer_error,
            remote_model_activity='not_proven_by_local_liveness',
            heartbeat_interval_seconds=self.heartbeat_seconds)
        for suffix,key in [('.stdout','stdout_bytes'),('.stderr','stderr_bytes')]:
            p=Path(str(self.stem)+suffix);row[key]=p.stat().st_size if p.exists() else 0
        live=Path(str(self.stem)+'.progress.json');temp=Path(str(live)+'.tmp')
        temp.write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(live)
        if terminal or now>=self.next_heartbeat:
            with Path(str(self.stem)+'.heartbeats.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(row,ensure_ascii=False)+'\n')
            self.next_heartbeat=now+self.heartbeat_seconds
        return row

    def _loop(self):
        while not self.stop.wait(self.tick_seconds):
            try:self.snapshot()
            except Exception as error:self.observer_error=type(error).__name__

    def __enter__(self):
        try:self.snapshot()
        except Exception as error:self.observer_error=type(error).__name__
        self.thread=threading.Thread(target=self._loop,daemon=True)
        try:self.thread.start()
        except Exception as error:self.observer_error=type(error).__name__;self.thread=None
        return self

    def finish(self,terminal):
        self.stop.set()
        if self.thread:self.thread.join(timeout=10)
        if self.thread and self.thread.is_alive():
            self.observer_error='observer_thread_not_stopped'
            return {'observer_error':self.observer_error}
        try:return self.snapshot(terminal)
        except Exception as error:
            self.observer_error=type(error).__name__
            return {'observer_error':self.observer_error}
