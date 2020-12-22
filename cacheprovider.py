class JenkinsLFPlugin:
    """ Plugin which implements the --lf (run last-failing) option """
    def __init__(self, config, filename):
        self.config = config
        active_key = 'lf'
        self.active = config.getvalue(active_key)
        if self.active:
            self.lastfailed = config.cache.get("cache/{}".format(filename), {})
        else:
            self.lastfailed = {}

    def pytest_report_header(self):
        if self.active:
            if not self.lastfailed:
                mode = "no recorded failures"
            else:
                mode = "rerun last %d failures" % len(self.lastfailed)
            return "run-last-failure: %s" % mode

    def pytest_runtest_logreport(self, report):
        if hasattr(report, "wasxfail"):
            if "failed to start: exited abnormally" in report.wasxfail:
                self.lastfailed[report.nodeid] = True
        if report.failed and "xfail" not in report.keywords:
            self.lastfailed[report.nodeid] = True
        elif not report.failed:
            if report.when == "call":
                self.lastfailed.pop(report.nodeid, None)

    def pytest_collectreport(self, report):
        passed = report.outcome in ('passed', 'skipped')
        if passed:
            if report.nodeid in self.lastfailed:
                self.lastfailed.pop(report.nodeid)
                self.lastfailed.update(
                    (item.nodeid, True)
                    for item in report.result)
        else:
            self.lastfailed[report.nodeid] = True

    def pytest_collection_modifyitems(self, session, config, items):
        if self.active:
            if self.lastfailed:
                previously_failed = []
                previously_passed = []
                for item in items:
                    if item.nodeid in self.lastfailed:
                        previously_failed.append(item)
                    else:
                        previously_passed.append(item)
                if previously_failed:
                    items[:] = previously_failed
                    config.hook.pytest_deselected(items=previously_passed)
            else:
                config.hook.pytest_deselected(items=items)
                items[:] = []

    def pytest_sessionfinish(self, session):
        config = self.config
        if config.getvalue("cacheshow") or hasattr(config, "slaveinput"):
            return
        prev_failed = config.cache.get(
            "cache/{}".format(config.lastfailed_file), None
        ) is not None
        if (session.testscollected and prev_failed) or self.lastfailed:
            config.cache.set(
                "cache/{}".format(config.lastfailed_file), self.lastfailed
            )