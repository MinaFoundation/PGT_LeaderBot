from invoke import task


@task
def read(ctx):
    ctx.run("python github_tracker_bot/read_sheet.py")


@task
def test(ctx):
    ctx.run("python -m unittest discover tests")


@task
def testbot(ctx):
    ctx.run(f"python -m unittest tests/test_bot_unit.py")


@task
def testbotint(ctx):
    ctx.run(f"python -m unittest tests/test_bot_integration.py")


@task
def testmongo(ctx):
    ctx.run(f"python -m unittest tests/test_mongo_data_handler.py")


@task
def testmongoint(ctx):
    ctx.run(f"python -m unittest tests/test_mongo_integration.py")

@task
def testextract(ctx):
    ctx.run(f"python -m unittest tests/test_extract_unnecessary_diff.py")

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
def botf(ctx):
    ctx.run("python github_tracker_bot/bot_functions.py")


@task
def decide(ctx):
    ctx.run("python github_tracker_bot/ai_decide_commits.py")


@task
def leaderbot(ctx):
    ctx.run("python leader_bot/bot.py")


@task
def shfunc(ctx):
    ctx.run("python leader_bot/sheet_functions.py")


@task
def dbf(ctx):
    ctx.run("python leader_bot/db_functions.py")


@task
def lbf(ctx):
    ctx.run("python leader_bot/leaderboard_functions.py")
