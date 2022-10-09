// "timeago"
var units = {
	year: 24 * 60 * 60 * 1000 * 365,
	month: (24 * 60 * 60 * 1000 * 365) / 12,
	day: 24 * 60 * 60 * 1000,
	hour: 60 * 60 * 1000,
	minute: 60 * 1000,
	second: 1000,
};

var rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

var getRelativeTime = (d1, d2 = new Date()) => {
	var elapsed = d1 - d2;

	for (var u in units)
		if (Math.abs(elapsed) > units[u] || u == "second")
			return rtf.format(Math.round(elapsed / units[u]), u);
};

times = document.getElementsByTagName("time");
skipIntervalWait(updateTimes, 10000);

function skipIntervalWait(updateTimes, t) {
	updateTimes();
	return setInterval(updateTimes, t);
}

function updateTimes() {
	Array.from(times).forEach(function (element) {
		element.innerHTML = getRelativeTime(element.dateTime * 1000);
	});
}

// search users

window.addEventListener("load", () => {
	const searchForm = document.querySelector("#search");
	const searchContainer = document.querySelector("#search-container");

	async function doSearch(search) {
		var url = "/search/post";

		const response = await fetch(url, {
			method: "POST",
			body: JSON.stringify(search),
			headers: {
				"Content-Type": "application/json",
			},
		});

		Object.entries(await response.json()).forEach(([key, value]) => {
			const newSearchResultElement = document.createElement("div");
			newSearchResultElement.className = "list-item search-result";

			const newSearchResultElementUser = document.createElement("a");
			newSearchResultElementUser.href = "/user/" + value["id"];
			newSearchResultElementUser.innerHTML = value["username"];
			newSearchResultElement.appendChild(newSearchResultElementUser);

			const newSearchResultElementCreatedAt = document.createElement("time");
			newSearchResultElementCreatedAt.className = "timeago account_registered";
			newSearchResultElementCreatedAt.dateTime = value["created_at"];
			newSearchResultElement.appendChild(newSearchResultElementCreatedAt);

			searchContainer.appendChild(newSearchResultElement);

			// update "x [time] ago"
			updateTimes();
		});
	}

	if (searchForm) {
		searchForm.addEventListener("keypress", function (e) {
			if (e.key === "Enter") {
				e.preventDefault();
				doSearch({ search: searchForm.value });
				// clear search form
				searchForm.value = "";
				// clear search results
				searchContainer.replaceChildren();
			}
		});
	}
});
