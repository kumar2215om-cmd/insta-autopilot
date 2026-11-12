# ReplyInbox SEO launch checklist

The SEO pages (features, comparisons, guides, sitemap, robots.txt, llms.txt, structured data) live on this
`seo-launch` branch and are NOT on the live site yet. Do these steps once replyinbox.in works (KYC done).

1. Point replyinbox.in at the likhodm Vercel project (Domains), and check https://replyinbox.in opens the site.
2. In Vercel → likhodm → Environment Variables, add `SITE_URL=https://replyinbox.in` (Production).
3. Redirect likhodm.vercel.app to replyinbox.in (Vercel → Domains → redirect), so search engines see one address.
4. Merge this branch into `main` (GitHub → Pull request from `seo-launch` → Merge). That deploys everything.
5. Check: https://replyinbox.in/sitemap.xml, /robots.txt, /llms.txt, /guides, /glossary and the six topic hubs
   (/instagram-dm-automation, /instagram-lead-generation, /sell-on-instagram, /ai-instagram-dm-replies,
   /instagram-dm-automation-tools, /instagram-automation-by-industry) all open. Test one page in Google's Rich Results Test.
6. Google Search Console: add the domain, verify it, submit https://replyinbox.in/sitemap.xml.
7. Bing Webmaster Tools: import from Search Console (Bing also feeds ChatGPT search).
8. Re-check competitor prices on the /vs/ pages (seo_content.py, `CHECKED`) and update the date.
9. List ReplyInbox on Product Hunt, G2, Capterra and post in creator communities, so AI assistants and Google see it mentioned.
