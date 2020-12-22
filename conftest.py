import os
import datetime
import logging
import pytest

from cacheprovider import JenkinsLFPlugin
from logger import Logger


log = logging.getLogger(__name__)


def pytest_sessionstart(session):

    session.run_duration = datetime.datetime.now()
    print(u"\nPytest session start %s\n" % session.run_duration)


@pytest.mark.trylast
def pytest_sessionfinish(session):
    finish = datetime.datetime.now()
    duration = datetime.timedelta(
        seconds=(finish - session.run_duration).seconds
    )
    print(u"\n\nPytest session finish %s (duration=%s)\n" % (finish, duration))


@pytest.hookimpl
def pytest_addoption(parser):
    parser.addoption(
        "--capturelog",
        dest="logger",
        default=None,
        action="store_true",
        help="Show log messages for each failed test"
    )
    parser.addoption(
        "--fail-debug-info",
        action="store_true",
        help="Show screenshot and test case urls for each failed test"
    )
    parser.addoption(
        '--jlf-filename',
        action='store',
        dest="jlf",
        metavar="str",
        help="rerun only the tests that failed at the last run"
             " (or none if none failed)"
    )
    parser.addoption(
        '--prod',
        action="store_true",
        help="run tests with production config-settings"
    )
    parser.addoption(
        '--stage',
        action="store_true",
        help="run tests with stage config-settings"
    )


@pytest.fixture(autouse=True)
def logger(request):
    return logging.getLogger()


@pytest.mark.tryfirst
@pytest.mark.hookwrapper
def pytest_runtest_makereport(item):
    """pytest failed test report generator"""
    html_plugin = item.config.pluginmanager.getplugin('html')
    outcome = yield
    report = outcome.get_result()
    when = report.when
    extra = getattr(report, 'extra', [])
    if when == "call" and not report.passed:
        if item.config.getoption("--fail-debug-info"):
            if hasattr(item.config, "get_fail_debug"):
                fail_debug = item.config.get_fail_debug()
                test_case_url = None
                pytest_failed_test_command = None
                if fail_debug[0] == 'LuckyLabs':
                    (
                        test_case_url,
                        pytest_failed_test_command,
                    ) = fail_debug[1:]
                test_case = (
                    u"\nTEST CASE: {}".format(test_case_url)
                    if test_case_url else u''
                )
                run_test_command = (
                    u"\nPYTEST COMMAND: {}".format(
                        pytest_failed_test_command
                    )
                )
                fail_info = (
                    (
                        u"{test_case_url}"
                        u"{run_test_command}"
                    ).format(
                        test_case_url=test_case,
                        run_test_command=run_test_command,
                    )
                )
                extra.append(html_plugin.extras.url(
                    test_case_url, name=u"TEST CASE"
                ))
                report.extra = extra

                longrepr = getattr(report, 'longrepr', None)
                if hasattr(longrepr, 'addsection'):
                    longrepr.sections.insert(
                        0, (u"Captured stdout %s" % when, fail_info, u"-")
                    )


def pytest_configure(config):
    if config.getoption("--capturelog"):
        config.pluginmanager.register(Logger(), "logger")
    config.lastfailed_file = "lastfailed"
    if config.getoption("--jlf-filename"):
        filename = config.getoption("--jlf-filename")
        config.lastfailed_file = filename
        config.pluginmanager.register(
            JenkinsLFPlugin(config, filename), "jlfplugin"
        )
    if config.getoption("--prod"):
        os.environ['ENVIRONMENT'] = 'PROD'
    if config.getoption("--stage"):
        os.environ['ENVIRONMENT'] = 'STAGE'