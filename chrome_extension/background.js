chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "analyzeNews") {
        fetch("http://127.0.0.1:8000/biasbuster/analyze_news/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ news_text: request.text })
        })
        .then(response => response.json())
        .then(data => sendResponse({ result: data }))
        .catch(error => sendResponse({ error: "Failed to analyze news." }));
        return true;
    }
});
