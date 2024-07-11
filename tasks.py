from invoke import task


@task
def read(ctx):
    ctx.run("python github_tracker_bot/read_sheet.py")


@task
def test(ctx):
    ctx.run("python -m unittest discover tests")
