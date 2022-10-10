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

// handle form input etc

window.addEventListener("load", () => {
	// remove this if you figure it out in css
	document.querySelector("#userthreads").children[1].children.length == 0
		? (document.querySelector("#userthreads").style.backgroundColor =
				"transparent")
		: () => {};
	document.querySelector("#watched-user-threads").children[1].children.length ==
	0
		? (document.querySelector("#watched-user-threads").style.backgroundColor =
				"transparent")
		: () => {};

	const searchForm = document.querySelector("#search-form").children[0];
	const searchContainer = document.querySelector("#search-container");

	const searchFollowedForm =
		document.querySelector("#search-followed").children[0];

	const threadForm = document.querySelector("#start-thread").children[0];
	const threadContainer = document.querySelector("#thread-container");

	async function handleForm(input, url) {
		const response = await fetch(url, {
			method: "POST",
			body: JSON.stringify(input),
			headers: {
				"Content-Type": "application/json",
			},
		});

		switch (url) {
			case "/search/post":
				updateSearchContainer(response, searchContainer);
				break;
			case "/thread/post":
				console.log("hmm");
				break;
			//updateThreadContainer(response, threadContainer);
		}
	}

	if (searchForm) {
		searchForm.addEventListener("keypress", function (e) {
			if (e.key === "Enter") {
				e.preventDefault();
				handleForm({ search: searchForm.value }, "/search/post");
				// clear search form
				searchForm.value = "";
				// clear search results
				searchContainer.replaceChildren();
				searchContainer.style.transform = "scaleY(1)";
			}
		});
	}
	if (threadForm) {
		threadForm.addEventListener("keypress", function (e) {
			if (e.key === "Enter") {
				e.preventDefault();
				if (threadForm.value.length == 0) {
					alert("threads or replies can't be empty");
					threadForm.value = "";
					return;
				}
				handleForm({ message: threadForm.value }, "/thread/post");
				// clear thread form
				threadForm.value = "";
			}
		});
	}
	if (searchFollowedForm) {
		searchFollowedForm.addEventListener("keypress", function (e) {
			if (e.key === "Enter") {
				e.preventDefault();
				alert("not implemented yet");
				searchFollowedForm.value = "";
				return;
			}
		});
	}
});

async function updateSearchContainer(response, container) {
	const timeout = (ms) => new Promise((r) => setTimeout(r, ms));
	document.querySelector("#search-results").style.backgroundColor =
		"hsl(var(--main-bg-color-hs), 15%)";

	for (const user of await response.json()) {
		const newSearchResultElement = document.createElement("div");
		newSearchResultElement.className = "list-item search-result new-item";

		const newSearchResultElementUser = document.createElement("a");
		newSearchResultElementUser.href = "/user/" + user.id;
		newSearchResultElementUser.innerHTML = user.username;
		newSearchResultElement.appendChild(newSearchResultElementUser);

		const newSearchResultElementCreatedAt = document.createElement("time");
		newSearchResultElementCreatedAt.className = "timeago account_registered";
		newSearchResultElementCreatedAt.dateTime = user.created_at;
		newSearchResultElement.appendChild(newSearchResultElementCreatedAt);

		container.appendChild(newSearchResultElement);

		// update "x [time] ago"
		updateTimes();

		// for style
		await timeout(50);
	}
}
