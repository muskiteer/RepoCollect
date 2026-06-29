RepoCollect - Build a single source of truth for your engineering knowledge.


Discord Steps 
Step 1: Create a Discord Application
Go to the Discord Developer Portal.
Click New Application.
Give it a name.
Click Create.
Step 2: Create the Bot
Open your application.
Go to Bot.
Click Add Bot.

You now have a bot user.

Step 3: Get the Bot Token

In the Bot page:

Click Reset Token (or View Token if available).
Copy it.

Example:

MTExMjM0NTY3ODkw...

Save it:

export DISCORD_TOKEN="YOUR_BOT_TOKEN"
Step 4: Enable Message Content Intent

Go to:

Bot → Privileged Gateway Intents

Enable:

✅ Message Content Intent

Click Save Changes.

Without this, the API returns:

"content": ""

instead of the actual message text.

Step 5: Generate an Invite Link

Go to:

OAuth2 → URL Generator

Scopes

Select:

✅ bot

(Optional)

✅ applications.commands
Bot Permissions

Only these are required:

✅ View Channels
✅ Read Message History

No Administrator permission is needed.

Step 6: Invite the Bot

Copy the generated URL.

It will look like:

https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=66560

Open it in your browser.

Choose your server.

Click Authorize.

Your bot should appear in the member list.

Step 7: Verify the Bot Can See the Channel

Right-click the channel.

Edit Channel

Permissions

Ensure the bot has

View Channel
Read Message History

If the channel is private, explicitly allow the bot.