"""
Unit tests for progress report background tasks.
"""
from django.test import TestCase
from mock import Mock, MagicMock, patch, ANY, call
from contextlib import nested
from django.test.utils import override_settings
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from opaque_keys import InvalidKeyError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from pgreport.tasks import (
    update_table_task, create_report_task, update_table_task_for_active_course,
    ProgressreportException, ProgressReportTask, TaskState,
    BaseProgressReportTask
)
from pgreport.views import UserDoesNotExists
import datetime
from pytz import UTC
import StringIO
import uuid

class TaskStateTestCase(TestCase):
    """Test TaskState class"""
    def setUp(self):
        patcher0 = patch('pgreport.tasks.cache')
        self.cache_mock = patcher0.start()
        self.addCleanup(patcher0.stop)

    def tearDown(self):
        pass

    def test_is_active(self):
        self.cache_mock.get.return_value = {"course_id": "date"}
        state = TaskState("task_name", "course_id")
        result = state.is_active
        self.assertEquals(result, True)
        self.cache_mock.get.assert_called_once_with(key=state.key, default={})

        self.cache_mock.get.return_value = None
        result = state.is_active
        self.assertEquals(result, False)
        
    def test_set_task_state(self):
        self.cache_mock.get.return_value = {"course_id": "date"}
        state = TaskState("task_name", "course_id2")
        state.set_task_state()
        self.cache_mock.set.assert_called_with(key=state.key, value={
            'course_id': 'date', 'course_id2': ANY})

        self.cache_mock.get.return_value = None
        state.set_task_state()
        self.cache_mock.set.assert_called_with(key=state.key, value={
            'course_id2': ANY})

    def test_delete_task_state(self):
        self.cache_mock.get.return_value = {"course_id": "date", "course_id2": "date"}
        state = TaskState("task_name", "course_id")
        state.delete_task_state()
        self.assertEquals(self.cache_mock.delete.call_count, 0)

        self.cache_mock.get.return_value = {} 
        state = TaskState("task_name", "course_id")
        state.delete_task_state()
        self.cache_mock.delete.assert_called_once_with(key=state.key)


class BaseProgressReportTaskTestCase(TestCase):
    """Test BaseProgressReportTask class"""
    def setUp(self):
        pass
       
    def tearDown(self):
        pass

    @patch('pgreport.tasks.TaskState')
    def test_delete_task_state(self, state_mock):
        base = BaseProgressReportTask()
        base._delete_task_state(args=["task_name", "course_id"])
        state_mock.assert_called_with(ANY, "course_id")

        base._delete_task_state(args=None)
        state_mock.assert_called_with(ANY, "AllCourses")

    @patch('pgreport.tasks.BaseProgressReportTask._delete_task_state')
    def test_on_success(self, del_mock):
        base = BaseProgressReportTask()
        base.on_success("retval", "task_id", "args", "kwargs")
        del_mock.assert_called_once_with("args")

    @patch('pgreport.tasks.BaseProgressReportTask._delete_task_state')
    def test_on_failure(self, del_mock):
        base = BaseProgressReportTask()
        base.on_failure("exc", "task_id", "args", "kwargs", "einfo")
        del_mock.assert_called_once_with("args")

@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class ProgressReportTaskTestCase(ModuleStoreTestCase):
    """Test ProgressReportTask class"""
    COURSE_NAME = "test_task"

    def setUp(self):
        self.course1 = CourseFactory.create(display_name=self.COURSE_NAME + "1")
        self.course2 = CourseFactory.create(display_name=self.COURSE_NAME + "2")
        self.course3 = CourseFactory.create(display_name=self.COURSE_NAME + "3")
        self.course4 = CourseFactory.create(display_name=self.COURSE_NAME + "4")
        self.course1.start  = datetime.datetime(100, 12, 31, 0, 0, tzinfo=UTC)
        self.course1.end = datetime.datetime(2999, 12, 31, 0, 0, tzinfo=UTC)
        self.course2.start  = datetime.datetime(100, 12, 31, 0, 0, tzinfo=UTC)
        self.course2.end = None
        self.course3.start  = datetime.datetime(100, 12, 31, 0, 0, tzinfo=UTC)
        self.course3.end = datetime.datetime(1000, 12, 31, 0, 0, tzinfo=UTC)
        self.course4.start  = datetime.datetime(2030, 1, 1, tzinfo=UTC)
        self.course4.end = None
        self.courses = [self.course1, self.course2, self.course3, self.course4]    
        self.func_mock = MagicMock()
        self.task_id = str(uuid.uuid4())

        patcher0 = patch('pgreport.tasks.cache')
        self.cache_mock = patcher0.start()
        self.addCleanup(patcher0.stop)

    def tearDown(self):
        pass

    def test_ProgressReportTask_init(self):
        task = ProgressReportTask(self.func_mock)

        fake_func = lambda x: x
        msg = "^Funcion is not celery task.$"
        with self.assertRaisesRegexp(ProgressreportException, msg):
            task = ProgressReportTask(fake_func)
        
    @patch('pgreport.tasks.TaskState')
    def test_send_task(self, ts_mock):
        task = ProgressReportTask(self.func_mock)
        with patch('sys.stdout', new_callable=StringIO.StringIO) as std_mock:
            ts_mock().is_active = False
            task.send_task(self.course1.id)

        ts_mock.assert_called_with(task.task_name, self.course1.id)
        ts_mock().set_task_state.assert_called_once_with()
        self.func_mock.apply_async.assert_called_with(
            args=(ANY, unicode(self.course1.id)), task_id=ANY, expires=23.5*60*60, retry=False
        )
        self.assertEquals(std_mock.getvalue(),
            "Send task (task_id: %s)\n" % (self.func_mock.apply_async().id)
        )

        with patch('sys.stdout', new_callable=StringIO.StringIO) as std_mock:
            ts_mock().is_active = True
            task.send_task(self.course1.id)

        self.assertEquals(std_mock.getvalue(),
            "Task is already running. (%s, %s)\n" % (task.task_name, self.course1.id)
        )

    @patch('pgreport.tasks.ProgressReportTask.send_task') 
    @patch('pgreport.tasks.modulestore') 
    def test_send_tasks(self, module_mock, send_mock):
        task = ProgressReportTask(self.func_mock)
        module_mock().get_courses.return_value = self.courses

        task.send_tasks()
        module_mock.assert_called_with(task.modulestore_name)
        module_mock().get_courses.assert_called_once_with()
        send_mock.assert_has_calls([call(self.course1.id), call(self.course2.id)])

    def test_show_task_status(self):
        task = ProgressReportTask(self.func_mock)
        with patch('sys.stdout', new_callable=StringIO.StringIO) as std_mock:
            result_mock = MagicMock()
            result_mock.state = "PENDING"
            self.func_mock.AsyncResult.return_value = result_mock 
            task.show_task_status("task_id")

        self.func_mock.AsyncResult.assert_called_once_with("task_id")
        self.assertEquals(std_mock.getvalue(),
            "Task not found or PENDING state\n"
        )

        with patch('sys.stdout', new_callable=StringIO.StringIO) as std_mock:
            result_mock = MagicMock()
            result_mock.state = "SUCCESS"
            self.func_mock.AsyncResult.return_value = result_mock 
            task.show_task_status("task_id")

        self.assertEquals(std_mock.getvalue(),
            "Current State: {}, {}\n".format(result_mock.state, result_mock.info)
        )

    def test_show_task_list(self):
        task = ProgressReportTask(self.func_mock)
        with nested(
            patch('sys.stdout', new_callable=StringIO.StringIO),
            patch('pgreport.tasks.celery')
        ) as (std_mock, cel_mock):
            stat_mock = MagicMock()
            stat_mock.active.return_value = {"queue": None}
            cel_mock.control.inspect.return_value = stat_mock
            task.show_task_list()    

        cel_mock.control.inspect.assert_called_once_with()
        self.assertEquals(std_mock.getvalue(),
            "*** Active queues ***\n{}: []\n".format("queue")
        )

        status = {
            "args": "argment",
            "id": "task_id",
            "name": "task_name",
            "worker_pid": "worker_pid",
        }
        with nested(
            patch('sys.stdout', new_callable=StringIO.StringIO),
            patch('pgreport.tasks.celery')
        ) as (std_mock, cel_mock):
            stat_mock = MagicMock()
            stat_mock.active.return_value = {"queue": [status]}
            cel_mock.control.inspect.return_value = stat_mock
            task.show_task_list()    

        self.assertEquals(std_mock.getvalue(),
            '*** Active queues ***\nqueue: [\n * Task id: {id}, Task args: {args},  Task name: {name}, Worker pid: {worker_pid}\n]\n'.format(**status)
        )

    def test_revoke_task(self):
        task = ProgressReportTask(self.func_mock)
        task.revoke_task("task_id")    
        self.func_mock.AsyncResult.assert_called_once_with("task_id")
        self.func_mock.AsyncResult().revoke.assert_called_once_with(terminate=True)

    @patch('pgreport.tasks.os')
    @patch('pgreport.tasks.socket')
    @patch('pgreport.tasks.update_pgreport_table')
    def test_update_table_task(self, update_mock, socket_mock, os_mock):
        result = update_table_task(self.task_id, self.course1.id)
        update_mock.assert_called_once_with(self.course1.id, ANY)
        socket_mock.gethostname.assert_called_once_with()
        os_mock.getpid.assert_called_once_with()
        self.assertEquals(result, "Update complete!!! (%s)" % self.course1.id)

        msg = "Test update_table_task!"
        update_mock.side_effect = UserDoesNotExists(msg)
        result = update_table_task(self.task_id, self.course1.id)
        self.assertEquals(result, "%s (%s)" % (msg, self.course1.id))

    @patch('pgreport.tasks.os')
    @patch('pgreport.tasks.socket')
    @patch('pgreport.tasks.create_pgreport_csv')
    def test_create_report_task(self, create_mock, socket_mock, os_mock):
        result = create_report_task(self.task_id, self.course1.id)
        create_mock.assert_called_once_with(self.course1.id, ANY)
        socket_mock.gethostname.assert_called_once_with()
        os_mock.getpid.assert_called_once_with()
        self.assertEquals(result, "Create complete!!! (%s)" % self.course1.id)

        msg = "Test create_report_task!"
        create_mock.side_effect = UserDoesNotExists(msg)
        result = create_report_task(self.task_id, self.course1.id)
        self.assertEquals(result, "%s (%s)" % (msg, self.course1.id))

    def test_update_table_task_for_active_course(self):
        task_mock = MagicMock()
        with patch('pgreport.tasks.ProgressReportTask',
             return_value=task_mock) as prt_mock:

            update_table_task_for_active_course()
            prt_mock.assert_called_once_with(update_table_task)
            task_mock.send_tasks.assert_called_once_with()
