#requires -Version 7.2
# Suspended launch, non-breakaway Job Object, verified whole-tree termination.
param([Parameter(Mandatory)][string]$SpecFile)
$ErrorActionPreference='Stop'
$s=Get-Content -LiteralPath $SpecFile -Raw | ConvertFrom-Json
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Text;
using System.Diagnostics;
using System.Runtime.InteropServices;
public static class AuthorJobProcess {
 [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Startup {
  public int cb; public string reserved,desktop,title; public int x,y,cx,cy,xc,yc,fill,flags;
  public short show,reserved2; public IntPtr reservedPtr,stdin,stdout,stderr;
 }
 [StructLayout(LayoutKind.Sequential)] struct ProcessInfo {public IntPtr process,thread;public uint pid,tid;}
 [StructLayout(LayoutKind.Sequential)] struct BasicLimit {
  public long processTime,jobTime; public uint flags; public UIntPtr minWS,maxWS;
  public uint processLimit; public UIntPtr affinity; public uint priority,scheduling;
 }
 [StructLayout(LayoutKind.Sequential)] struct Io {public ulong a,b,c,d,e,f;}
 [StructLayout(LayoutKind.Sequential)] struct ExtendedLimit {
  public BasicLimit basic; public Io io; public UIntPtr processMemory,jobMemory,peakProcess,peakJob;
 }
 [StructLayout(LayoutKind.Sequential)] struct Accounting {
  public long user,kernel,periodUser,periodKernel;public uint faults,total,active,terminated;
 }
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcessW(string exe,StringBuilder args,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref Startup si,out ProcessInfo pi);
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr CreateJobObjectW(IntPtr security,IntPtr name);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int cls,ref ExtendedLimit info,int size);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool QueryInformationJobObject(IntPtr job,int cls,out Accounting info,int size,IntPtr length);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateJobObject(IntPtr job,uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateProcess(IntPtr process,uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle,uint ms);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr process,out uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetHandleInformation(IntPtr handle,uint mask,uint flags);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
 public class Receipt {
  public int exitCode=2; public string reason=null; public uint pid; public double seconds;
  public bool stdinRequired,stdinComplete,cleanupConfirmed,terminationRequested,suspendedAssignment;
  public string cleanupScope="windows-job-object"; public uint? activeProcessesAfterCleanup;
  public string stdinDelivery="inherited-file-with-EOF";
 }
 static void Check(bool ok,string what) {if(!ok)throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error(),what);}
 static string Quote(string arg) {
  var b=new StringBuilder("\"");int n=0;
  foreach(char c in arg){if(c=='\\'){n++;continue;}if(c=='\"'){b.Append('\\',2*n+1);b.Append(c);}else{b.Append('\\',n);b.Append(c);}n=0;}
  b.Append('\\',2*n);b.Append('"');return b.ToString();
 }
 static uint Active(IntPtr job) {Accounting a;Check(QueryInformationJobObject(job,1,out a,Marshal.SizeOf(typeof(Accounting)),IntPtr.Zero),"Query job");return a.active;}
 public static Receipt Run(string exe,string[] args,string cwd,string output,string error,string input,double timeout,long limit) {
  var r=new Receipt {stdinRequired=!String.IsNullOrEmpty(input),stdinComplete=String.IsNullOrEmpty(input)};
  var watch=Stopwatch.StartNew();IntPtr job=IntPtr.Zero;ProcessInfo pi=new ProcessInfo();bool assigned=false,started=false;
  FileStream o=null,e=null,i=null;
  try {
   o=new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.ReadWrite);
   e=new FileStream(error,FileMode.CreateNew,FileAccess.Write,FileShare.ReadWrite);
   i=new FileStream(r.stdinRequired?input:"NUL",FileMode.Open,FileAccess.Read,FileShare.ReadWrite);
   if(r.stdinRequired && i.Length>1048576)throw new InvalidOperationException("stdin size limit");
   foreach(var f in new[]{i,o,e})Check(SetHandleInformation(f.SafeFileHandle.DangerousGetHandle(),1,1),"Set inherited handle");
   job=CreateJobObjectW(IntPtr.Zero,IntPtr.Zero);Check(job!=IntPtr.Zero,"Create job");
   var limits=new ExtendedLimit();limits.basic.flags=0x2000;
   Check(SetInformationJobObject(job,9,ref limits,Marshal.SizeOf(typeof(ExtendedLimit))),"Set job limits");
   var si=new Startup {cb=Marshal.SizeOf(typeof(Startup)),flags=0x100,
    stdin=i.SafeFileHandle.DangerousGetHandle(),stdout=o.SafeFileHandle.DangerousGetHandle(),stderr=e.SafeFileHandle.DangerousGetHandle()};
   var command=new StringBuilder(Quote(exe));foreach(var arg in args)command.Append(" ").Append(Quote(arg));
   Check(CreateProcessW(exe,command,IntPtr.Zero,IntPtr.Zero,true,0x08000004,IntPtr.Zero,cwd,ref si,out pi),"Create suspended process");
   started=true;r.pid=pi.pid;
   Check(AssignProcessToJobObject(job,pi.process),"Assign suspended process");assigned=true;r.suspendedAssignment=true;
   Check(ResumeThread(pi.thread)!=0xffffffff,"Resume process");
   // The complete immutable file and EOF are available via the inherited handle.
   // This records delivery, not a claim that the model consumed the prompt.
   r.stdinComplete=true;
   while(WaitForSingleObject(pi.process,200)==258) {
    if(watch.Elapsed.TotalSeconds>timeout){r.reason="timeout";break;}
    if(o.Length+e.Length>limit){r.reason="output_limit";break;}
   }
   if(r.reason!=null){r.terminationRequested=true;Check(TerminateJobObject(job,124),"Terminate job");}
   Check(WaitForSingleObject(pi.process,10000)==0,"Wait for owned exit");
   uint code;Check(GetExitCodeProcess(pi.process,out code),"Read exit");r.exitCode=r.reason!=null?124:unchecked((int)code);
   if(o.Length+e.Length>limit){r.reason="output_limit";r.exitCode=124;}
  } catch(Exception ex) {r.reason=ex.Message;r.exitCode=2;}
  finally {
   try {
    if(assigned) {
     if(Active(job)>0){r.terminationRequested=true;Check(TerminateJobObject(job,124),"Final job cleanup");}
     var cleanup=Stopwatch.StartNew();uint active;
     while((active=Active(job))>0 && cleanup.Elapsed.TotalSeconds<10)System.Threading.Thread.Sleep(50);
     r.activeProcessesAfterCleanup=active;r.cleanupConfirmed=active==0;
    } else if(started){TerminateProcess(pi.process,2);WaitForSingleObject(pi.process,10000);}
   } catch(Exception ex){r.cleanupConfirmed=false;r.reason="cleanup_unverified: "+ex.Message;}
   if(!r.cleanupConfirmed){r.reason="cleanup_unverified";r.exitCode=2;}
   else if(r.stdinRequired && !r.stdinComplete){r.reason="stdin_delivery_unverified";r.exitCode=2;}
   if(pi.thread!=IntPtr.Zero)CloseHandle(pi.thread);if(pi.process!=IntPtr.Zero)CloseHandle(pi.process);
   if(job!=IntPtr.Zero)CloseHandle(job);if(i!=null)i.Dispose();if(o!=null)o.Dispose();if(e!=null)e.Dispose();
   r.seconds=watch.Elapsed.TotalSeconds;
  }
  return r;
 }
}
'@
$r=[AuthorJobProcess]::Run($s.exe,[string[]]$s.arguments,$s.cwd,$s.stdout,$s.stderr,$s.inputFile,[double]$s.timeout,[long]$s.outputBytes)
$r | ConvertTo-Json -Compress | Set-Content -LiteralPath $s.receipt -Encoding utf8NoBOM
exit $r.exitCode
