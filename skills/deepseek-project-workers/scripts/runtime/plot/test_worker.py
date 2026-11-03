"""Protocol boundary checks. No network/model inference in these tests."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import plot_worker as w


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.schema=w.read(w.HERE/'layout_schema.json')
        self.layout=dict(axis_font=11,tick_font=10,legend_font=10,left=.24,right=.98,
                         bottom=.23,top=.97,xlabel_pad=3,ylabel_pad=3,legend_loc='upper right')

    def test_valid(self):
        w.validate_layout(self.layout,self.schema)

    def test_reject_scientific_key(self):
        with self.assertRaises(ValueError):
            w.validate_layout(dict(self.layout,thermal_scale=.9),self.schema)

    def test_nonfinite_bool_and_budget_bounds(self):
        for v in [float('nan'),float('inf'),True,30]:
            with self.subTest(value=v),self.assertRaises(ValueError):
                w.validate_layout(dict(self.layout,tick_font=v),self.schema)

    def test_wrong_model_outcome_and_error(self):
        model=dict(providerID='opencode-go',id='deepseek-v4.1-flash',variant='max')
        session=dict(info=dict(id='ses_test',outcome='succeeded',model=model),messages=[dict(type='assistant',model=model)])
        events=[dict(type='text',sessionID='ses_test')]
        w.validate_session(events,session)
        for key,value in [('variant','high'),('providerID','other')]:
            bad=copy.deepcopy(session); bad['info']['model'][key]=value
            with self.assertRaises(ValueError):w.validate_session(events,bad)
        with self.assertRaises(ValueError): w.validate_session(events+[dict(type='error')],session)
        session['info']['outcome']='failed'
        with self.assertRaises(ValueError):w.validate_session(events,session)

    def test_bounded_two_role_revision(self):
        # Real render orchestration, mocked model transport. Exercise revise->accept,
        # independent role payload, image-only probe gate and hard three-round cap.
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp); w.write(run/'schema.json',self.schema);(run/'adapter.py').write_text('# fixed adapter',encoding='utf-8')
            worker=w.Worker(dict(max_rounds=3,initial_layout=self.layout,task='test'),run,'unused','unused')
            seen=[]
            def render(layout,n):
                out=run/f'{n:02}_render';out.mkdir()
                Image.new('RGB',(600,400),'white').save(out/'preview.png')
                return out,dict(passed=True)
            def turn(role,n,prompt,attachments):
                seen.append((role,n))
                if role=='A':return dict(layout=self.layout,summary='layout')
                self.assertNotIn('layout author summary',prompt)
                self.assertEqual(Path(attachments[0]).name,'review_sheet.png')
                return dict(verdict='revise' if n==1 else 'accept',vision_probe='ABCDEF',findings=[])
            with patch.object(worker,'render',side_effect=render),patch.object(worker,'turn',side_effect=turn),patch.object(w.secrets,'token_hex',return_value='abcdef'):
                result=worker.execute()
            self.assertEqual(result['rounds'],2)
            self.assertEqual(seen,[('A',1),('B',1),('A',2),('B',2)])

    def test_unread_image_cannot_pass(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp);w.write(run/'schema.json',self.schema);(run/'adapter.py').write_text('# fixed adapter',encoding='utf-8')
            worker=w.Worker(dict(max_rounds=1,initial_layout=self.layout,task='test'),run,'unused','unused')
            def render(layout,n):
                out=run/f'{n:02}_render';out.mkdir();Image.new('RGB',(600,400),'white').save(out/'preview.png')
                return out,dict(passed=True)
            def turn(role,*args):
                return dict(layout=self.layout) if role=='A' else dict(verdict='accept',vision_probe='wrong',findings=[])
            with patch.object(worker,'render',side_effect=render),patch.object(worker,'turn',side_effect=turn),self.assertRaisesRegex(ValueError,'vision probe'):
                worker.execute()


if __name__=='__main__':unittest.main(verbosity=2)
