from pybuilder.core import use_plugin, init
import inspect, os, sys

#my_location = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
#sys.path.append(my_location)
#sys.path.append(my_location + '/../quant_container')

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.distutils")
use_plugin('python.pycharm')

name = "msq-domain"
default_task = "publish"

@init
def initialize(project):
    project.depends_on('cloudpickle')
    project.depends_on('aiokafka',version = "==0.2.1")
    project.depends_on('kafka',version = "==1.3.1")
    project.depends_on('mockito')

    project.set_property('dir_source_main_python','src')
    project.set_property('dir_source_unittest_python', 'unit_tests')
    project.set_property('dir_source_main_scripts', 'scripts')
