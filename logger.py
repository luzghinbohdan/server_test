import logging
import py
import pytest
import re

from functools import wraps


log = logging.getLogger(__name__)
MAX_SYMBOLS = 255


class LoggerFilter(logging.Filter):

    def filter(self, record):
        return record.levelno > 20


class Logger(object):

    def pytest_runtest_setup(self, item):
        item.capturelog_handler = LoggerHandler()
        item.capturelog_handler.setFormatter(logging.Formatter(
            u"%(asctime)-12s%(levelname)-8s%(message)s\n", u"%H:%M:%S"
        ))
        root_logger = logging.getLogger()
        item.capturelog_handler.addFilter(LoggerFilter())
        root_logger.addHandler(item.capturelog_handler)
        root_logger.setLevel(logging.NOTSET)

    @pytest.mark.hookwrapper
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if hasattr(item, "capturelog_handler"):
            if call.when == 'teardown':
                root_logger = logging.getLogger()
                root_logger.removeHandler(item.capturelog_handler)
            if not report.passed:
                longrepr = getattr(report, 'longrepr', None)
                if hasattr(longrepr, 'addsection'):
                    captured_log = item.capturelog_handler.stream.getvalue()
                    if captured_log:
                        longrepr.sections.insert(
                            len(longrepr.sections),
                            (u'Captured log', u"\n%s" % captured_log, u"-")
                        )
            if call.when == 'teardown':
                item.capturelog_handler.close()
                del item.capturelog_handler


class LoggerHandler(logging.StreamHandler):

    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.stream = py.io.TextIO()
        self.records = []

    def close(self):
        logging.StreamHandler.close(self)
        self.stream.close()


def request_logging(request, *args, **kwargs):
    content = request.content.decode('utf-8')
    log.info(
        "STATUS CODE: {status_code}\n"
        "{tabs}HEADERS: {headers}\n"
        "{tabs}METHOD: {method}\n"
        "{tabs}LINK: {link}\n"
        "{tabs}BODY: {body}\n"
        "{tabs}RESPONSE CONTENT: "
        "{content}{ellipsis} ({length} symbols)\n"
        "{tabs}RESPONSE HEADERS: {response_headers}\n"
        .format(
            status_code=request.status_code,
            headers=request.request.headers,
            method=request.request.method,
            link=request.url,
            body=request.request.body,
            content=re.sub(r'\s+', ' ', content)[:MAX_SYMBOLS],
            ellipsis=(
                " ..." if len(request.content) > MAX_SYMBOLS else ""
            ),
            length=len(request.content),
            tabs=" " * 12,
            response_headers=request.headers
        )
    )


def qa_api_logger(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        log.info(u'[QA API] Run: {} return: {}'.format(func.__name__, res))
        return res

    return wrapper