from invoke import task


@task
def read(ctx):
    ctx.run("python github_tracker_bot/read_sheet.py")


@task
def test(ctx):
    ctx.run("python -m unittest discover tests")


@task
def testredis(ctx):
    ctx.run(f"python -m unittest tests/test_redis_data_handler.py")


@task
def testss(ctx):
    ctx.run(f"python -m unittest tests/test_spreadsheet_to_list_of_user.py")


@task
def commit(ctx):
    ctx.run("python github_tracker_bot/commit_scraper.py")


@task
def process(ctx):
    ctx.run("python github_tracker_bot/process_commits.py")


@task
def bot(ctx):
    ctx.run("python github_tracker_bot/bot.py")


@task
def decide(ctx):
    ctx.run("python github_tracker_bot/ai_decide_commits.py")
