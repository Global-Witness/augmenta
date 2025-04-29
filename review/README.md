# Reviewing classifications

Large Language Models are still often wrong. They may hallucinate information or they may [misunderstand your instructions](/docs/prompt.md).

If you use the classified data in outputs were accuracy is crucial, you should review the classifications.

There are several ways to do this. This directory contains one of them, a Google Apps Script.

Create a new Google Sheet and copy your `output_csv` to it. Create a few new empty columns: `review_status`, `review_user`, `review_notes` and `review_timestamp`.

In the Google Sheet, go to Extensions > Apps Script. Overwrite the default `Code.gs` with the contents of [`Code.gs`](Code.gs). Create a new file called `Index.html` and copy the contents of [`Index.html`](Index.html) into it. Save the project.

Click on "Deploy" > "New deployment". Click on "Select type" and choose "Web app". Give it a name, choose who should have access, and click "Deploy".

You should get a URL you can share with your colleagues, allowing you to concurrently review the classifications.