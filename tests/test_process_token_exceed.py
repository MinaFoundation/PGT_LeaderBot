import unittest
import tiktoken
import config
import github_tracker_bot.helpers.extract_unnecessary_diff as extractor
import github_tracker_bot.helpers.calculate_token as calculator
import github_tracker_bot.helpers.handle_daily_commits_exceed_data as handler
import github_tracker_bot.prompts as prompts

from openai import AuthenticationError, NotFoundError, OpenAI, OpenAIError


class TestProcessTokenExceed(unittest.TestCase):
    def setUp(self):
        def generate_data_with_token_count(token_count):
            return "word " * (token_count - 1)

        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.ok_commit_data = {
            "2024-04-29": [
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "berkingurcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T16:52:07Z",
                    "message": "ADD string for message",
                    "sha": "94f79d4689ebdde3b48ec672cf784fd48ad0b14c",
                    "branch": "main",
                    "diff": 'diff --git a/packages/chain/src/messages.ts b/packages/chain/src/messages.ts\nindex c5f8680..fc77753 100644\n--- a/packages/chain/src/messages.ts\n+++ b/packages/chain/src/messages.ts\n@@ -1,6 +1,6 @@\n import { runtimeModule, state, runtimeMethod, Runtime, RuntimeModule } from "@proto-kit/module";\n import { State, StateMap, assert } from "@proto-kit/protocol";\n-import { Bool, Field, Struct } from "o1js";\n+import { Bool, Field, Struct, CircuitString } from "o1js";\n \n export class Agent extends Struct({\n     agentId: Field,\n@@ -21,7 +21,7 @@ export class Agent extends Struct({\n \n export class MessageDetail extends Struct({\n     agent: Agent,\n-    message: Field,\n+    message: String,\n }) {\n     \n }\n@@ -31,10 +31,11 @@ export class Message extends Struct({\n     messageDetails: MessageDetail\n }) {\n     public isValid(): Bool {\n-        const a = this.messageDetails.message.greaterThan(99999999999)\n-        const b = this.messageDetails.message.lessThan(1000000000000)\n+        const desiredLength = new Field(12);\n+        const message = this.messageDetails.message;\n+        const len = new Field(message.length)\n \n-        return a.and(b)\n+        return len.equals(desiredLength);\n     }\n }\n \n\n diff --git a/packages/chain/test/messages.test.ts b/packages/chain/test/messages.test.ts\nindex f62a395..3a1600d 100644\n--- a/packages/chain/test/messages.test.ts\n+++ b/packages/chain/test/messages.test.ts\n@@ -1,5 +1,5 @@\n import { TestingAppChain } from "@proto-kit/sdk";\n-import { Field, PrivateKey, UInt64 } from "o1js";\n+import { Field, PrivateKey, UInt64, CircuitString } from "o1js";\n import { Messages, Agent, Message, MessageDetail } from "../src/messages";\n import { log } from "@proto-kit/common";\n \n@@ -23,6 +23,11 @@ describe("Mina Spy Chain Messages", () => {\n     let messages: any;\n     let agents: Agent[];\n \n+    function generateMessage(input: string) {\n+        const message = input\n+        return message\n+    }\n+\n     beforeAll(async () => {\n         await appChain.start();\n \n@@ -34,7 +39,7 @@ describe("Mina Spy Chain Messages", () => {\n         messages = appChain.runtime.resolve("Messages");\n     \n         agents = []\n-    \n+\n         for (let i = 1; i <= 5; i++) {\n             agents.push(new Agent({\n                 agentId: Field(i),\n@@ -66,7 +71,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(1),\n             messageDetails: new MessageDetail({\n                 agent: agents[0],\n-                message: Field(100000000001)\n+                message: generateMessage("SECRETMeSSGE")\n             })\n         });\n     \n@@ -110,7 +115,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(2),\n             messageDetails: {\n                 agent: wrongSecurityAgent,\n-                message: Field(100000000001)\n+                message: generateMessage("ZAAAAAAAAAAA")\n             }\n         });\n \n@@ -129,7 +134,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(3),\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(999)\n+                message: generateMessage("AAA")\n             }\n         });\n \n@@ -149,7 +154,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(0), // Lower than last valid\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(120000000001)\n+                message: generateMessage("CCCCCCCCCCCC")\n             }\n         });\n     \n@@ -173,7 +178,7 @@ describe("Mina Spy Chain Messages", () => {\n                     lastMessageNumber: Field(0),\n                     securityCode: Field(10)\n                 }),\n-                message: Field(100000000001)\n+                message: generateMessage("AAAAAAAAAAAA")\n             }\n         });',
                },
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "Berkin G\u00fcrcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T16:52:31Z",
                    "message": "Merge pull request #1 from berkingurcan/string-message\n\nADD string for message",
                    "sha": "558c1ba6511f618d1eed0ce8d2675ddaa47fa039",
                    "branch": "main",
                    "diff": 'diff --git a/packages/chain/src/messages.ts b/packages/chain/src/messages.ts\nindex c5f8680..fc77753 100644\n--- a/packages/chain/src/messages.ts\n+++ b/packages/chain/src/messages.ts\n@@ -1,6 +1,6 @@\n import { runtimeModule, state, runtimeMethod, Runtime, RuntimeModule } from "@proto-kit/module";\n import { State, StateMap, assert } from "@proto-kit/protocol";\n-import { Bool, Field, Struct } from "o1js";\n+import { Bool, Field, Struct, CircuitString } from "o1js";\n \n export class Agent extends Struct({\n     agentId: Field,\n@@ -21,7 +21,7 @@ export class Agent extends Struct({\n \n export class MessageDetail extends Struct({\n     agent: Agent,\n-    message: Field,\n+    message: String,\n }) {\n     \n }\n@@ -31,10 +31,11 @@ export class Message extends Struct({\n     messageDetails: MessageDetail\n }) {\n     public isValid(): Bool {\n-        const a = this.messageDetails.message.greaterThan(99999999999)\n-        const b = this.messageDetails.message.lessThan(1000000000000)\n+        const desiredLength = new Field(12);\n+        const message = this.messageDetails.message;\n+        const len = new Field(message.length)\n \n-        return a.and(b)\n+        return len.equals(desiredLength);\n     }\n }\n \n\n diff --git a/packages/chain/test/messages.test.ts b/packages/chain/test/messages.test.ts\nindex f62a395..3a1600d 100644\n--- a/packages/chain/test/messages.test.ts\n+++ b/packages/chain/test/messages.test.ts\n@@ -1,5 +1,5 @@\n import { TestingAppChain } from "@proto-kit/sdk";\n-import { Field, PrivateKey, UInt64 } from "o1js";\n+import { Field, PrivateKey, UInt64, CircuitString } from "o1js";\n import { Messages, Agent, Message, MessageDetail } from "../src/messages";\n import { log } from "@proto-kit/common";\n \n@@ -23,6 +23,11 @@ describe("Mina Spy Chain Messages", () => {\n     let messages: any;\n     let agents: Agent[];\n \n+    function generateMessage(input: string) {\n+        const message = input\n+        return message\n+    }\n+\n     beforeAll(async () => {\n         await appChain.start();\n \n@@ -34,7 +39,7 @@ describe("Mina Spy Chain Messages", () => {\n         messages = appChain.runtime.resolve("Messages");\n     \n         agents = []\n-    \n+\n         for (let i = 1; i <= 5; i++) {\n             agents.push(new Agent({\n                 agentId: Field(i),\n@@ -66,7 +71,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(1),\n             messageDetails: new MessageDetail({\n                 agent: agents[0],\n-                message: Field(100000000001)\n+                message: generateMessage("SECRETMeSSGE")\n             })\n         });\n     \n@@ -110,7 +115,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(2),\n             messageDetails: {\n                 agent: wrongSecurityAgent,\n-                message: Field(100000000001)\n+                message: generateMessage("ZAAAAAAAAAAA")\n             }\n         });\n \n@@ -129,7 +134,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(3),\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(999)\n+                message: generateMessage("AAA")\n             }\n         });\n \n@@ -149,7 +154,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(0), // Lower than last valid\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(120000000001)\n+                message: generateMessage("CCCCCCCCCCCC")\n             }\n         });\n     \n@@ -173,7 +178,7 @@ describe("Mina Spy Chain Messages", () => {\n                     lastMessageNumber: Field(0),\n                     securityCode: Field(10)\n                 }),\n-                message: Field(100000000001)\n+                message: generateMessage("AAAAAAAAAAAA")\n             }\n         });',
                },
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "Berkin G\u00fcrcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T17:54:59Z",
                    "message": "Update README.md",
                    "sha": "79937f5f2b9d4042e14891daa26e51cd36076e67",
                    "branch": "main",
                    "diff": "diff --git a/README.md b/README.md\nindex bf02f21..f3f981b 100644\n--- a/README.md\n+++ b/README.md\n@@ -1,7 +1,11 @@\n-# Protokit starter-kit\n+# MINA NAVIGATORS L2E CHALLENGE 3\n \n-This repository is a monorepo aimed at kickstarting application chain development using the Protokit framework.\n+This repository is a solution for Mina Navigators program, learn to earn challenge 3.\n \n+## Answer to the question regarding privacy\n+This app chain is not private regarding messages, agents and their contents because all inputs and states are public. It is roughly solved by encrypting and decrypting by content and secret codes BUT it is not tricky and also we need verification of the messages. So, it is solved by benefiting zk programs, messages should go through verifiable computation on to ensure their privacy and only the proof of this computation should be transferred. By using this technique, all existing message constraints can be confirmed, and without disclosing any sensitive information, the system's state can be updated as necessary. Then we can change the application messages and their verification are private.\n+\n+ \n ## Quick start\n \n The monorepo contains 1 package and 1 app:\n@@ -21,33 +25,8 @@ The monorepo contains 1 package and 1 app:\n > `docker run -it --rm -p 3000:3000 -p 8080:8080 -v %cd%:/starter-kit -w /starter-kit gplane/pnpm:node18 bash`\n \n \n-### Setup\n-\n-```zsh\n-git clone https://github.com/proto-kit/starter-kit my-chain\n-cd my-chain\n-\n-# ensures you have the right node.js version\n-nvm use\n-pnpm install\n-```\n-\n-### Running the sequencer & UI\n-\n-```zsh\n-# starts both UI and sequencer locally\n-pnpm dev\n-\n-# starts UI only\n-pnpm dev -- --filter web\n-# starts sequencer only\n-pnpm dev -- --filter chain\n-```\n-\n ### Running tests\n ```zsh\n # run and watch tests for the `chain` package\n-pnpm run test --filter=chain -- --watchAll\n+pnpm run test\n ```\n-\n-Navigate to `localhost:3000` to see the example UI, or to `localhost:8080/graphql` to see the GQL interface of the locally running sequencer.",
                },
            ]
        }

        too_long_words = generate_data_with_token_count(130000)
        self.exceeded_commit_data = {
            "2024-04-29": [
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "berkingurcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T16:52:07Z",
                    "message": "ADD string for message",
                    "sha": "94f79d4689ebdde3b48ec672cf784fd48ad0b14c",
                    "branch": "main",
                    "diff": 'diff --git a/packages/chain/src/messages.ts b/packages/chain/src/messages.ts\nindex c5f8680..fc77753 100644\n--- a/packages/chain/src/messages.ts\n+++ b/packages/chain/src/messages.ts\n@@ -1,6 +1,6 @@\n import { runtimeModule, state, runtimeMethod, Runtime, RuntimeModule } from "@proto-kit/module";\n import { State, StateMap, assert } from "@proto-kit/protocol";\n-import { Bool, Field, Struct } from "o1js";\n+import { Bool, Field, Struct, CircuitString } from "o1js";\n \n export class Agent extends Struct({\n     agentId: Field,\n@@ -21,7 +21,7 @@ export class Agent extends Struct({\n \n export class MessageDetail extends Struct({\n     agent: Agent,\n-    message: Field,\n+    message: String,\n }) {\n     \n }\n@@ -31,10 +31,11 @@ export class Message extends Struct({\n     messageDetails: MessageDetail\n }) {\n     public isValid(): Bool {\n-        const a = this.messageDetails.message.greaterThan(99999999999)\n-        const b = this.messageDetails.message.lessThan(1000000000000)\n+        const desiredLength = new Field(12);\n+        const message = this.messageDetails.message;\n+        const len = new Field(message.length)\n \n-        return a.and(b)\n+        return len.equals(desiredLength);\n     }\n }\n \n\n diff --git a/packages/chain/test/messages.test.ts b/packages/chain/test/messages.test.ts\nindex f62a395..3a1600d 100644\n--- a/packages/chain/test/messages.test.ts\n+++ b/packages/chain/test/messages.test.ts\n@@ -1,5 +1,5 @@\n import { TestingAppChain } from "@proto-kit/sdk";\n-import { Field, PrivateKey, UInt64 } from "o1js";\n+import { Field, PrivateKey, UInt64, CircuitString } from "o1js";\n import { Messages, Agent, Message, MessageDetail } from "../src/messages";\n import { log } from "@proto-kit/common";\n \n@@ -23,6 +23,11 @@ describe("Mina Spy Chain Messages", () => {\n     let messages: any;\n     let agents: Agent[];\n \n+    function generateMessage(input: string) {\n+        const message = input\n+        return message\n+    }\n+\n     beforeAll(async () => {\n         await appChain.start();\n \n@@ -34,7 +39,7 @@ describe("Mina Spy Chain Messages", () => {\n         messages = appChain.runtime.resolve("Messages");\n     \n         agents = []\n-    \n+\n         for (let i = 1; i <= 5; i++) {\n             agents.push(new Agent({\n                 agentId: Field(i),\n@@ -66,7 +71,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(1),\n             messageDetails: new MessageDetail({\n                 agent: agents[0],\n-                message: Field(100000000001)\n+                message: generateMessage("SECRETMeSSGE")\n             })\n         });\n     \n@@ -110,7 +115,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(2),\n             messageDetails: {\n                 agent: wrongSecurityAgent,\n-                message: Field(100000000001)\n+                message: generateMessage("ZAAAAAAAAAAA")\n             }\n         });\n \n@@ -129,7 +134,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(3),\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(999)\n+                message: generateMessage("AAA")\n             }\n         });\n \n@@ -149,7 +154,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(0), // Lower than last valid\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(120000000001)\n+                message: generateMessage("CCCCCCCCCCCC")\n             }\n         });\n     \n@@ -173,7 +178,7 @@ describe("Mina Spy Chain Messages", () => {\n                     lastMessageNumber: Field(0),\n                     securityCode: Field(10)\n                 }),\n-                message: Field(100000000001)\n+                message: generateMessage("AAAAAAAAAAAA")\n             }\n         });',
                },
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "Berkin G\u00fcrcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T16:52:31Z",
                    "message": "Merge pull request #1 from berkingurcan/string-message\n\nADD string for message",
                    "sha": "558c1ba6511f618d1eed0ce8d2675ddaa47fa039",
                    "branch": "main",
                    "diff": 'diff --git a/packages/chain/src/messages.ts b/packages/chain/src/messages.ts\nindex c5f8680..fc77753 100644\n--- a/packages/chain/src/messages.ts\n+++ b/packages/chain/src/messages.ts\n@@ -1,6 +1,6 @@\n import { runtimeModule, state, runtimeMethod, Runtime, RuntimeModule } from "@proto-kit/module";\n import { State, StateMap, assert } from "@proto-kit/protocol";\n-import { Bool, Field, Struct } from "o1js";\n+import { Bool, Field, Struct, CircuitString } from "o1js";\n \n export class Agent extends Struct({\n     agentId: Field,\n@@ -21,7 +21,7 @@ export class Agent extends Struct({\n \n export class MessageDetail extends Struct({\n     agent: Agent,\n-    message: Field,\n+    message: String,\n }) {\n     \n }\n@@ -31,10 +31,11 @@ export class Message extends Struct({\n     messageDetails: MessageDetail\n }) {\n     public isValid(): Bool {\n-        const a = this.messageDetails.message.greaterThan(99999999999)\n-        const b = this.messageDetails.message.lessThan(1000000000000)\n+        const desiredLength = new Field(12);\n+        const message = this.messageDetails.message;\n+        const len = new Field(message.length)\n \n-        return a.and(b)\n+        return len.equals(desiredLength);\n     }\n }\n \n\n diff --git a/packages/chain/test/messages.test.ts b/packages/chain/test/messages.test.ts\nindex f62a395..3a1600d 100644\n--- a/packages/chain/test/messages.test.ts\n+++ b/packages/chain/test/messages.test.ts\n@@ -1,5 +1,5 @@\n import { TestingAppChain } from "@proto-kit/sdk";\n-import { Field, PrivateKey, UInt64 } from "o1js";\n+import { Field, PrivateKey, UInt64, CircuitString } from "o1js";\n import { Messages, Agent, Message, MessageDetail } from "../src/messages";\n import { log } from "@proto-kit/common";\n \n@@ -23,6 +23,11 @@ describe("Mina Spy Chain Messages", () => {\n     let messages: any;\n     let agents: Agent[];\n \n+    function generateMessage(input: string) {\n+        const message = input\n+        return message\n+    }\n+\n     beforeAll(async () => {\n         await appChain.start();\n \n@@ -34,7 +39,7 @@ describe("Mina Spy Chain Messages", () => {\n         messages = appChain.runtime.resolve("Messages");\n     \n         agents = []\n-    \n+\n         for (let i = 1; i <= 5; i++) {\n             agents.push(new Agent({\n                 agentId: Field(i),\n@@ -66,7 +71,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(1),\n             messageDetails: new MessageDetail({\n                 agent: agents[0],\n-                message: Field(100000000001)\n+                message: generateMessage("SECRETMeSSGE")\n             })\n         });\n     \n@@ -110,7 +115,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(2),\n             messageDetails: {\n                 agent: wrongSecurityAgent,\n-                message: Field(100000000001)\n+                message: generateMessage("ZAAAAAAAAAAA")\n             }\n         });\n \n@@ -129,7 +134,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(3),\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(999)\n+                message: generateMessage("AAA")\n             }\n         });\n \n@@ -149,7 +154,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(0), // Lower than last valid\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(120000000001)\n+                message: generateMessage("CCCCCCCCCCCC")\n             }\n         });\n     \n@@ -173,7 +178,7 @@ describe("Mina Spy Chain Messages", () => {\n                     lastMessageNumber: Field(0),\n                     securityCode: Field(10)\n                 }),\n-                message: Field(100000000001)\n+                message: generateMessage("AAAAAAAAAAAA")\n             }\n         });',
                },
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "Berkin G\u00fcrcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T17:54:59Z",
                    "message": "Update README.md",
                    "sha": "1111111111111111111111111111111111111111",
                    "branch": "main",
                    "diff": "diff --git a/packages/chain/src/messages.ts b/packages/chain/src/messages.ts\n "
                    + too_long_words,
                },
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "Berkin G\u00fcrcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T17:54:59Z",
                    "message": "Update README.md",
                    "sha": "79937f5f2b9d4042e14891daa26e51cd36076e67",
                    "branch": "main",
                    "diff": "diff --git a/README.md b/README.md\nindex bf02f21..f3f981b 100644\n--- a/README.md\n+++ b/README.md\n@@ -1,7 +1,11 @@\n-# Protokit starter-kit\n+# MINA NAVIGATORS L2E CHALLENGE 3\n \n-This repository is a monorepo aimed at kickstarting application chain development using the Protokit framework.\n+This repository is a solution for Mina Navigators program, learn to earn challenge 3.\n \n+## Answer to the question regarding privacy\n+This app chain is not private regarding messages, agents and their contents because all inputs and states are public. It is roughly solved by encrypting and decrypting by content and secret codes BUT it is not tricky and also we need verification of the messages. So, it is solved by benefiting zk programs, messages should go through verifiable computation on to ensure their privacy and only the proof of this computation should be transferred. By using this technique, all existing message constraints can be confirmed, and without disclosing any sensitive information, the system's state can be updated as necessary. Then we can change the application messages and their verification are private.\n+\n+ \n ## Quick start\n \n The monorepo contains 1 package and 1 app:\n@@ -21,33 +25,8 @@ The monorepo contains 1 package and 1 app:\n > `docker run -it --rm -p 3000:3000 -p 8080:8080 -v %cd%:/starter-kit -w /starter-kit gplane/pnpm:node18 bash`\n \n \n-### Setup\n-\n-```zsh\n-git clone https://github.com/proto-kit/starter-kit my-chain\n-cd my-chain\n-\n-# ensures you have the right node.js version\n-nvm use\n-pnpm install\n-```\n-\n-### Running the sequencer & UI\n-\n-```zsh\n-# starts both UI and sequencer locally\n-pnpm dev\n-\n-# starts UI only\n-pnpm dev -- --filter web\n-# starts sequencer only\n-pnpm dev -- --filter chain\n-```\n-\n ### Running tests\n ```zsh\n # run and watch tests for the `chain` package\n-pnpm run test --filter=chain -- --watchAll\n+pnpm run test\n ```\n-\n-Navigate to `localhost:3000` to see the example UI, or to `localhost:8080/graphql` to see the GQL interface of the locally running sequencer.",
                },
            ]
        }

        self.exceeded_two_commit_data = {
            "2024-04-29": [
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "berkingurcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T16:52:07Z",
                    "message": "ADD string for message",
                    "sha": "94f79d4689ebdde3b48ec672cf784fd48ad0b14c",
                    "branch": "main",
                    "diff": 'diff --git a/packages/chain/src/messages.ts b/packages/chain/src/messages.ts\nindex c5f8680..fc77753 100644\n--- a/packages/chain/src/messages.ts\n+++ b/packages/chain/src/messages.ts\n@@ -1,6 +1,6 @@\n import { runtimeModule, state, runtimeMethod, Runtime, RuntimeModule } from "@proto-kit/module";\n import { State, StateMap, assert } from "@proto-kit/protocol";\n-import { Bool, Field, Struct } from "o1js";\n+import { Bool, Field, Struct, CircuitString } from "o1js";\n \n export class Agent extends Struct({\n     agentId: Field,\n@@ -21,7 +21,7 @@ export class Agent extends Struct({\n \n export class MessageDetail extends Struct({\n     agent: Agent,\n-    message: Field,\n+    message: String,\n }) {\n     \n }\n@@ -31,10 +31,11 @@ export class Message extends Struct({\n     messageDetails: MessageDetail\n }) {\n     public isValid(): Bool {\n-        const a = this.messageDetails.message.greaterThan(99999999999)\n-        const b = this.messageDetails.message.lessThan(1000000000000)\n+        const desiredLength = new Field(12);\n+        const message = this.messageDetails.message;\n+        const len = new Field(message.length)\n \n-        return a.and(b)\n+        return len.equals(desiredLength);\n     }\n }\n \n\n diff --git a/packages/chain/test/messages.test.ts b/packages/chain/test/messages.test.ts\nindex f62a395..3a1600d 100644\n--- a/packages/chain/test/messages.test.ts\n+++ b/packages/chain/test/messages.test.ts\n@@ -1,5 +1,5 @@\n import { TestingAppChain } from "@proto-kit/sdk";\n-import { Field, PrivateKey, UInt64 } from "o1js";\n+import { Field, PrivateKey, UInt64, CircuitString } from "o1js";\n import { Messages, Agent, Message, MessageDetail } from "../src/messages";\n import { log } from "@proto-kit/common";\n \n@@ -23,6 +23,11 @@ describe("Mina Spy Chain Messages", () => {\n     let messages: any;\n     let agents: Agent[];\n \n+    function generateMessage(input: string) {\n+        const message = input\n+        return message\n+    }\n+\n     beforeAll(async () => {\n         await appChain.start();\n \n@@ -34,7 +39,7 @@ describe("Mina Spy Chain Messages", () => {\n         messages = appChain.runtime.resolve("Messages");\n     \n         agents = []\n-    \n+\n         for (let i = 1; i <= 5; i++) {\n             agents.push(new Agent({\n                 agentId: Field(i),\n@@ -66,7 +71,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(1),\n             messageDetails: new MessageDetail({\n                 agent: agents[0],\n-                message: Field(100000000001)\n+                message: generateMessage("SECRETMeSSGE")\n             })\n         });\n     \n@@ -110,7 +115,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(2),\n             messageDetails: {\n                 agent: wrongSecurityAgent,\n-                message: Field(100000000001)\n+                message: generateMessage("ZAAAAAAAAAAA")\n             }\n         });\n \n@@ -129,7 +134,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(3),\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(999)\n+                message: generateMessage("AAA")\n             }\n         });\n \n@@ -149,7 +154,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(0), // Lower than last valid\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(120000000001)\n+                message: generateMessage("CCCCCCCCCCCC")\n             }\n         });\n     \n@@ -173,7 +178,7 @@ describe("Mina Spy Chain Messages", () => {\n                     lastMessageNumber: Field(0),\n                     securityCode: Field(10)\n                 }),\n-                message: Field(100000000001)\n+                message: generateMessage("AAAAAAAAAAAA")\n             }\n         });',
                },
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "Berkin G\u00fcrcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T16:52:31Z",
                    "message": "Merge pull request #1 from berkingurcan/string-message\n\nADD string for message",
                    "sha": "558c1ba6511f618d1eed0ce8d2675ddaa47fa039",
                    "branch": "main",
                    "diff": 'diff --git a/packages/chain/src/messages.ts b/packages/chain/src/messages.ts\nindex c5f8680..fc77753 100644\n--- a/packages/chain/src/messages.ts\n+++ b/packages/chain/src/messages.ts\n@@ -1,6 +1,6 @@\n import { runtimeModule, state, runtimeMethod, Runtime, RuntimeModule } from "@proto-kit/module";\n import { State, StateMap, assert } from "@proto-kit/protocol";\n-import { Bool, Field, Struct } from "o1js";\n+import { Bool, Field, Struct, CircuitString } from "o1js";\n \n export class Agent extends Struct({\n     agentId: Field,\n@@ -21,7 +21,7 @@ export class Agent extends Struct({\n \n export class MessageDetail extends Struct({\n     agent: Agent,\n-    message: Field,\n+    message: String,\n }) {\n     \n }\n@@ -31,10 +31,11 @@ export class Message extends Struct({\n     messageDetails: MessageDetail\n }) {\n     public isValid(): Bool {\n-        const a = this.messageDetails.message.greaterThan(99999999999)\n-        const b = this.messageDetails.message.lessThan(1000000000000)\n+        const desiredLength = new Field(12);\n+        const message = this.messageDetails.message;\n+        const len = new Field(message.length)\n \n-        return a.and(b)\n+        return len.equals(desiredLength);\n     }\n }\n \n\n diff --git a/packages/chain/test/messages.test.ts b/packages/chain/test/messages.test.ts\nindex f62a395..3a1600d 100644\n--- a/packages/chain/test/messages.test.ts\n+++ b/packages/chain/test/messages.test.ts\n@@ -1,5 +1,5 @@\n import { TestingAppChain } from "@proto-kit/sdk";\n-import { Field, PrivateKey, UInt64 } from "o1js";\n+import { Field, PrivateKey, UInt64, CircuitString } from "o1js";\n import { Messages, Agent, Message, MessageDetail } from "../src/messages";\n import { log } from "@proto-kit/common";\n \n@@ -23,6 +23,11 @@ describe("Mina Spy Chain Messages", () => {\n     let messages: any;\n     let agents: Agent[];\n \n+    function generateMessage(input: string) {\n+        const message = input\n+        return message\n+    }\n+\n     beforeAll(async () => {\n         await appChain.start();\n \n@@ -34,7 +39,7 @@ describe("Mina Spy Chain Messages", () => {\n         messages = appChain.runtime.resolve("Messages");\n     \n         agents = []\n-    \n+\n         for (let i = 1; i <= 5; i++) {\n             agents.push(new Agent({\n                 agentId: Field(i),\n@@ -66,7 +71,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(1),\n             messageDetails: new MessageDetail({\n                 agent: agents[0],\n-                message: Field(100000000001)\n+                message: generateMessage("SECRETMeSSGE")\n             })\n         });\n     \n@@ -110,7 +115,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(2),\n             messageDetails: {\n                 agent: wrongSecurityAgent,\n-                message: Field(100000000001)\n+                message: generateMessage("ZAAAAAAAAAAA")\n             }\n         });\n \n@@ -129,7 +134,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(3),\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(999)\n+                message: generateMessage("AAA")\n             }\n         });\n \n@@ -149,7 +154,7 @@ describe("Mina Spy Chain Messages", () => {\n             messageNumber: Field(0), // Lower than last valid\n             messageDetails: {\n                 agent: agents[0],\n-                message: Field(120000000001)\n+                message: generateMessage("CCCCCCCCCCCC")\n             }\n         });\n     \n@@ -173,7 +178,7 @@ describe("Mina Spy Chain Messages", () => {\n                     lastMessageNumber: Field(0),\n                     securityCode: Field(10)\n                 }),\n-                message: Field(100000000001)\n+                message: generateMessage("AAAAAAAAAAAA")\n             }\n         });',
                },
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "Berkin G\u00fcrcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T17:54:59Z",
                    "message": "Update README.md",
                    "sha": "1111111111111111111111111111111111111111",
                    "branch": "main",
                    "diff": "diff --git a/packages/chain/src/messages.ts b/packages/chain/src/messages.ts\n "
                    + too_long_words,
                },
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "Berkin G\u00fcrcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T17:54:59Z",
                    "message": "Update README.md",
                    "sha": "79937f5f2b9d4042e14891daa26e51cd36076e67",
                    "branch": "main",
                    "diff": "diff --git a/README.md b/README.md\nindex bf02f21..f3f981b 100644\n--- a/README.md\n+++ b/README.md\n@@ -1,7 +1,11 @@\n-# Protokit starter-kit\n+# MINA NAVIGATORS L2E CHALLENGE 3\n \n-This repository is a monorepo aimed at kickstarting application chain development using the Protokit framework.\n+This repository is a solution for Mina Navigators program, learn to earn challenge 3.\n \n+## Answer to the question regarding privacy\n+This app chain is not private regarding messages, agents and their contents because all inputs and states are public. It is roughly solved by encrypting and decrypting by content and secret codes BUT it is not tricky and also we need verification of the messages. So, it is solved by benefiting zk programs, messages should go through verifiable computation on to ensure their privacy and only the proof of this computation should be transferred. By using this technique, all existing message constraints can be confirmed, and without disclosing any sensitive information, the system's state can be updated as necessary. Then we can change the application messages and their verification are private.\n+\n+ \n ## Quick start\n \n The monorepo contains 1 package and 1 app:\n@@ -21,33 +25,8 @@ The monorepo contains 1 package and 1 app:\n > `docker run -it --rm -p 3000:3000 -p 8080:8080 -v %cd%:/starter-kit -w /starter-kit gplane/pnpm:node18 bash`\n \n \n-### Setup\n-\n-```zsh\n-git clone https://github.com/proto-kit/starter-kit my-chain\n-cd my-chain\n-\n-# ensures you have the right node.js version\n-nvm use\n-pnpm install\n-```\n-\n-### Running the sequencer & UI\n-\n-```zsh\n-# starts both UI and sequencer locally\n-pnpm dev\n-\n-# starts UI only\n-pnpm dev -- --filter web\n-# starts sequencer only\n-pnpm dev -- --filter chain\n-```\n-\n ### Running tests\n ```zsh\n # run and watch tests for the `chain` package\n-pnpm run test --filter=chain -- --watchAll\n+pnpm run test\n ```\n-\n-Navigate to `localhost:3000` to see the example UI, or to `localhost:8080/graphql` to see the GQL interface of the locally running sequencer.",
                },
                {
                    "repo": "berkingurcan/mina-spy-chain",
                    "author": "Berkin G\u00fcrcan",
                    "username": "berkingurcan",
                    "date": "2024-04-29T17:54:59Z",
                    "message": "Update README.md",
                    "sha": "2222222222222222222222222222222222222222",
                    "branch": "main",
                    "diff": "diff --git a/packages/chain/src/messages.ts b/packages/chain/src/messages.ts\n "
                    + too_long_words
                    + too_long_words,
                },
            ]
        }

    def test_process_token_exceed_one_diff(self):
        not_exceed_commit = self.ok_commit_data["2024-04-29"][0]
        before_ok_commit = calculator.calculate_token_number(not_exceed_commit["diff"])
        self.assertEqual(before_ok_commit, True)

        filtered_ok_commit = extractor.filter_diffs(not_exceed_commit["diff"])
        filtered_ok_commit_token_count = calculator.calculate_token_number(
            filtered_ok_commit
        )
        self.assertEqual(filtered_ok_commit_token_count, True)

        commit = self.exceeded_commit_data["2024-04-29"][2]
        before_truncated_commit = calculator.calculate_token_number(commit["diff"])
        truncated_commit = extractor.filter_diffs(commit["diff"])
        token_count = calculator.calculate_token_number(truncated_commit)

        self.assertEqual(before_truncated_commit, False)
        self.assertEqual(token_count, True)

    def test_process_token_exceed_total_commit(self):
        before_token_count = calculator.calculate_token_number(
            str(self.exceeded_two_commit_data["2024-04-29"])
        )
        self.assertEqual(before_token_count, False)
        handled_daily_commit_data = handler.handle_daily_exceed_data(
            self.exceeded_two_commit_data["2024-04-29"]
        )
        token_count = calculator.calculate_token_number(str(handled_daily_commit_data))

        self.assertEqual(token_count, True)


if __name__ == "__main__":
    unittest.main()
