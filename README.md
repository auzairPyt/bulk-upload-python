[](https://i.imgur.com/xXy4lZl.jpg)

# Smartlead bulk uploader for Python

This script does the following:

1. Using your API key, verifies if the users already exist in Smartlead.
2. Automatically logs into each through OAuth if they do not exist in the Smartlead account.

### Features:

- It doesn't open Chrome windows, it does it all inside the terminal window.
- Has basic error checking and retrying of a single login until it's correctly processed.
- Will skip any address based on API call information.
- Counts progress as it goes.

### Notes:

- It needs feedback so if you encounter errors post the screenshot in your assigned Slack channel.
- It takes up to 90 minutes to be done, parallel processing may be implement later.
