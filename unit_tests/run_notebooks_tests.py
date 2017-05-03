from unittest import TestCase
import nbformat
import os
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError


class TestMarkoutMessage(TestCase):
    # Test for Sell in bps over intra-day to COB1
    def test_case_1(self):
        cwd = os.getcwd()
        print('***', cwd, '***')
        nb = nbformat.read(open('.\\msq-domain\\mosaicsmartdata\\unit_tests\\Test_run.ipynb'), as_version=4)
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')

        try:
            out = ep.preprocess(nb, {'metadata': {'path': '.\\msq-domain\\mosaicsmartdata\\unit_tests'}})
        except CellExecutionError:
            msg = 'Error executing the notebook "%s".\n\n'
            msg += 'See notebook "%s" for the traceback.'
            print(msg)
            raise
        finally:
            nbformat.write(nb, open('.\\msq-domain\\mosaicsmartdata\\unit_tests\\Test_run_result.ipynb', mode='wt'))