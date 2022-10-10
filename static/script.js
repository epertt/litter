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
	const searchForm = document.querySelector("#search-form").children[0];
	const searchContainer = document.querySelector("#search-container");

	const searchFollowedForm =
		document.querySelector("#search-followed").children[0];

	const threadForm = document.querySelector("#start-thread").children[0];
	const threadContainer = document.querySelector("#thread-container");

	async function handleForm(input, url, howmany) {
		const response = await fetch(url, {
			method: "POST",
			body: JSON.stringify(input),
			headers: {
				"Content-Type": "application/json",
			},
		});

		switch (url) {
			case "/search/post":
				updateSearchContainer(response, searchContainer, howmany);
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
				handleForm({ search: searchForm.value }, "/search/post", 0);
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
				handleForm({ message: threadForm.value }, "/thread/post", 0);
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

	// search on page load to display some recent users
	handleForm({ search: searchForm.value }, "/search/post", "5");
	searchContainer.style.transform = "scaleY(1)";
});

async function updateSearchContainer(response, container, howmany) {
	let i = 0;
	const timeout = (ms) => new Promise((r) => setTimeout(r, ms));

	document.querySelector("#search-results").style.backgroundColor =
		"hsl(var(--main-bg-color-hs), 15%)";

	for (const user of await response.json()) {
		if (i >= howmany && howmany != 0) {
			break;
		}

		console.log(user);

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

		i++;

		// for style
		await timeout(50);
	}

	// update "x [time] ago"
	updateTimes();
}
