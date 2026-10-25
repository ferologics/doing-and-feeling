// X thread exporter. Paste into the DevTools console on a logged-in https://x.com/<user>/status/<id> page.
//
// Scrolls the conversation, clicks the in-place "Show more replies" / "Show probable spam" /
// "Show additional replies" buttons, collects every post above the "Discover more" section, merges
// it with earlier runs (localStorage), and downloads the merged set as x-thread-export.json.
// Run it again on a sub-thread page to add that sub-thread. Reset with:
//     localStorage.removeItem("xThreadExport")
(async () => {
    const KEY = "xThreadExport";
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const store = JSON.parse(localStorage.getItem(KEY) || "{}");
    const before = Object.keys(store).length;

    const discoverHeading = () =>
        [...document.querySelectorAll("h2")].find((h) => /discover more|more posts/i.test(h.innerText));

    // Posts after the "Discover more" heading are unrelated recommendations.
    const inConversation = (el, heading) =>
        !heading || Boolean(heading.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_PRECEDING);

    const count = (article, testid) => {
        const label = article.querySelector(`[data-testid="${testid}"]`)?.getAttribute("aria-label") || "";
        return label.match(/^[\d,.]+[KM]?/)?.[0] || "0";
    };

    const scrape = () => {
        const heading = discoverHeading();
        for (const article of document.querySelectorAll('article[data-testid="tweet"]')) {
            if (!inConversation(article, heading)) continue;
            const time = article.querySelector("time");
            const url = time?.closest("a")?.href;
            if (!url || store[url]) continue;
            const texts = [...article.querySelectorAll('[data-testid="tweetText"]')];
            const card = article.querySelector('[data-testid="card.wrapper"]');
            store[url] = {
                url,
                author: article.querySelector('[data-testid="User-Name"]')?.innerText.replace(/\n+/g, " "),
                time: time.getAttribute("datetime"),
                text: texts[0]?.innerText || "",
                truncated: Boolean(article.querySelector('[data-testid="tweet-text-show-more-link"]')),
                links: [...(texts[0]?.querySelectorAll("a[href]") || [])].map((a) => ({ text: a.innerText, href: a.href })),
                quote: texts.slice(1).map((t) => t.innerText).join("\n---\n"),
                card: card?.innerText.replace(/\n+/g, " | ") || "",
                cardLink: card?.querySelector("a[href]")?.href || "",
                images: [...article.querySelectorAll('[data-testid="tweetPhoto"] img')].map((img) => img.alt),
                replies: count(article, "reply"),
                likes: count(article, "like") !== "0" ? count(article, "like") : count(article, "unlike"),
                page: location.href,
            };
        }
    };

    // Only in-place expanders; links like "Show replies" navigate away and would stop the script.
    const expand = () => {
        let clicked = 0;
        for (const el of document.querySelectorAll('[role="button"], button')) {
            if (el.closest("a")) continue;
            if (/^show (more replies|probable spam|additional replies)/i.test(el.innerText.trim())) {
                el.click();
                clicked++;
            }
        }
        return clicked;
    };

    for (let step = 0, idle = 0; step < 600 && idle < 6; step++) {
        scrape();
        if (expand()) {
            idle = 0;
            await sleep(2000);
            continue;
        }
        const heading = discoverHeading();
        if (heading && heading.getBoundingClientRect().top < window.innerHeight) break;
        const y = window.scrollY;
        window.scrollBy(0, window.innerHeight * 0.8);
        await sleep(1200);
        idle = window.scrollY === y ? idle + 1 : 0;
    }
    scrape();

    localStorage.setItem(KEY, JSON.stringify(store));
    const posts = Object.values(store);
    const blob = new Blob([JSON.stringify(posts, null, 2)], { type: "application/json" });
    const link = Object.assign(document.createElement("a"), {
        href: URL.createObjectURL(blob),
        download: "x-thread-export.json",
    });
    document.body.appendChild(link);
    link.click();
    link.remove();
    console.log(`x-thread-export: ${posts.length} posts (${posts.length - before} new this run) → Downloads/x-thread-export.json`);
})();
