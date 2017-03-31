from unittest import TestCase
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from nbconvert.preprocessors.execute import CellExecutionError


class TestMarkoutMessage(TestCase):
    # Test for Sell in bps over intra-day to COB1
    def test_case_1(self):

        nb = nbformat.read(open('../notebooks/Test_run.ipynb'), as_version=4)
        ep = ExecutePreprocessor(timeout=600, kernel_name='py35')

        try:
            out = ep.preprocess(nb, {'metadata': {'path': '../notebooks'}})
        except CellExecutionError:
            msg = 'Error executing the notebook "%s".\n\n'
            msg += 'See notebook "%s" for the traceback.'
            print(msg)
            raise
        finally:
            nbformat.write(nb, open('../notebooks/Test_run_result.ipynb', mode='wt'))