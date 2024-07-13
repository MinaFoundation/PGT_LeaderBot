DAILY_DECIDE_COMMIT_PROMPT = """
### **GitHub Commit Parameters**

During your development process, it's crucial that the code you add to the GitHub repositories makes sense and actually works. We really appreciate code that aims to make a difference and involves serious thinking behind it. Codes that require hard technical knowledge and deep thinking and are written with the aim of making a difference are the types of commits we're looking for from you. 

Here are the details regarding commit types that are not counted:

**Configuration Changes:** Adding/modifying Node IP, RPC endpoint, network ID, short name, API ID, title, etc. might not be accepted.

**Merge Conflict Commits:** Commits resolving conflicts but not containing actual progress or fixes might not be accepted.

**Revert or Undo Commits:** Commits reverting previous changes or correcting an error without adding new value to the project might not be accepted.

**Dependency Update Commits:** Commits that only include dependency updates and don’t contribute directly to the main project might not be accepted.

**Spam Commits:** Commits that repeatedly make very small or insignificant changes without contributing value to the project might not be accepted. For instance, commits focused solely on minor updates to the README file or superficial changes to wording or text that do not significantly impact the project's functionality might not be accepted.

Be really strict! If you believe the commit is really add features to the code then you can say it is qualified. Consider the diff file. Not consider only commit message.
""".trim()