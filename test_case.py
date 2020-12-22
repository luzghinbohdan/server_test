import pytest
import logging
import os


log = logging.getLogger(__name__)
ENV = os.environ.get('ENV')


class TestCase(object):
    test_case_url = ''
    path_to_test = None

    def get_path_to_test(self, method):
        return u"{path}.py -k {test_name}".format(
            path=u'/'.join(str(self.__module__).split(u'.')),
            test_name=method.__name__
        )

    def get_failed_test_command(self, name):
        if name == 'pytest':
            command = 'pytest'
        else:
            raise Exception('Name must be "pytest"')
        env = "ENV='{}'".format(ENV) if ENV else ''
        return (
            u"{env} {command} {path_to_test} --fail-debug-info --capturelog"
            .format(
                env=env,
                command=command,
                path_to_test=self.path_to_test
            )
        )


class BaseTestCase(TestCase):

    def setup_method(self, method):
        self.path_to_test = self.get_path_to_test(method)
        pytest.config.get_fail_debug = self.get_fail_debug

    def teardown_method(self, method):
        pass

    def get_fail_debug(self):
        """Failed test report generator"""
        pytest_failed_test_command = self.get_failed_test_command('pytest')
        return (
            'CompanyName',
            self.test_case_url,
            pytest_failed_test_command,
        )
