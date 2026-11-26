# Short address

The public demo's short address on Vercel. Vercel serves nothing itself: every request (the page, the chat
stream, sign-in, the Confirm click) is forwarded to the backend on Cloud Run, which still holds the sessions,
tools, checks and the model connection. The session cookie is set for the Vercel address, because the browser only
ever talks to it.

Deploy from this folder with the Vercel CLI, signed in to the project owner's account:

    cd vercel && npx vercel@latest --prod

To point the address at a new backend URL, change the destination in `vercel.json` and deploy again.
