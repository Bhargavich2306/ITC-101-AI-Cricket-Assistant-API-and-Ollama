// =========================================================
// SPORTS IQ - FRONTEND
// =========================================================

let matches = [];
let selectedMatch = null;
let currentMonth = new Date().toISOString().slice(0, 7);
let currentCommentary = "";
let squadCache = {};


// =========================================================
// HELPERS
// =========================================================

function $(id) {
    return document.getElementById(id);
}


function escapeHtml(value) {
    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function setText(id, value) {
    const element = $(id);

    if (element) {
        element.textContent =
            value === null ||
            value === undefined ||
            value === ""
                ? "—"
                : value;
    }
}


function formatScore(score, wickets) {

    if (
        score === null ||
        score === undefined ||
        score === ""
    ) {
        return "—";
    }

    return `${score}/${wickets ?? 0}`;
}


function formatOvers(overs) {

    if (
        overs === null ||
        overs === undefined ||
        overs === ""
    ) {
        return "—";
    }

    return `${overs} overs`;
}


function formatAnswer(text) {

    return escapeHtml(text)
        .replace(/\n\n/g, "</p><p>")
        .replace(/\n/g, "<br>");
}


function getInitials(name) {

    return String(name)
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map(word => word[0])
        .join("")
        .toUpperCase();
}


// =========================================================
// MONTH SELECTOR
// =========================================================

function setupMonthSelector() {

    let selector = $("monthSelector");

    if (!selector) {

        const sidebar = $("matchList");

        if (!sidebar) {
            return;
        }

        const wrapper =
            document.createElement("div");

        wrapper.className =
            "month-selector-wrapper";

        wrapper.innerHTML = `
            <label for="monthSelector">
                MATCH MONTH
            </label>

            <input
                type="month"
                id="monthSelector"
            >
        `;

        sidebar.parentNode.insertBefore(
            wrapper,
            sidebar
        );

        selector =
            $("monthSelector");
    }

    selector.value = currentMonth;

    selector.addEventListener(
        "change",
        () => {

            if (!selector.value) {
                return;
            }

            currentMonth =
                selector.value;

            loadMatches();
        }
    );
}


// =========================================================
// UPDATE SIDEBAR TITLE
// =========================================================

function updateMonthTitle() {

    const date =
        new Date(
            `${currentMonth}-01T00:00:00`
        );

    const monthName =
        date.toLocaleString(
            "en-US",
            {
                month: "long",
                year: "numeric"
            }
        );

    const headings =
        document.querySelectorAll(
            "h1, h2, h3"
        );

    headings.forEach(
        heading => {

            if (
                heading.textContent
                    .toUpperCase()
                    .includes("TODAY")
            ) {

                heading.textContent =
                    `${monthName} · INTERNATIONAL`;
            }
        }
    );
}


// =========================================================
// LOAD MONTH MATCHES
// =========================================================

async function loadMatches() {

    const list =
        $("matchList");

    if (list) {

        list.innerHTML = `
            <div class="players-loading">
                Loading international matches...
            </div>
        `;
    }

    updateMonthTitle();

    try {

        const response =
            await fetch(
                `/api/matches?month=${encodeURIComponent(currentMonth)}`,
                {
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (
            !response.ok ||
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Could not load matches."
            );
        }

        matches =
            Array.isArray(data.matches)
                ? data.matches
                : [];

        renderMatchList();

        if (matches.length > 0) {

            selectMatch(
                matches[0].id
            );

        } else {

            showNoMatches();
        }

    } catch (error) {

        console.error(
            "MONTH MATCH ERROR:",
            error
        );

        if (list) {

            list.innerHTML = `
                <div class="players-unavailable">
                    <strong>
                        Could not load international matches.
                    </strong>

                    <br><br>

                    Month:
                    ${escapeHtml(currentMonth)}

                    <br><br>

                    Make sure Flask and the Cricket API
                    are running.
                </div>
            `;
        }
    }
}


// =========================================================
// MATCH LIST
// =========================================================

function renderMatchList() {

    const list =
        $("matchList");

    if (!list) {
        return;
    }

    list.innerHTML = "";

    if (matches.length === 0) {

        showNoMatches();

        return;
    }

    matches.forEach(
        match => {

            const card =
                document.createElement(
                    "button"
                );

            card.type = "button";

            card.className =
                "match-card";

            card.dataset.matchId =
                match.id;

            const status =
                match.matchEnded
                    ? "ENDED"
                    : match.matchStarted
                        ? "LIVE"
                        : "UPCOMING";

            card.innerHTML = `

                <div class="match-card-type">
                    ${escapeHtml(
                        match.matchType ||
                        "INTERNATIONAL"
                    )}

                    ·

                    ${status}
                </div>

                <div class="match-card-title">
                    ${escapeHtml(match.team1)}
                    <br>
                    <strong>vs</strong>
                    <br>
                    ${escapeHtml(match.team2)}
                </div>

                <div class="match-card-score">

                    ${escapeHtml(
                        formatScore(
                            match.score1,
                            match.wickets1
                        )
                    )}

                    &nbsp;–&nbsp;

                    ${escapeHtml(
                        formatScore(
                            match.score2,
                            match.wickets2
                        )
                    )}

                </div>

                <div class="match-card-date">
                    ${escapeHtml(
                        match.date || ""
                    )}
                </div>
            `;

            card.addEventListener(
                "click",
                () => {
                    selectMatch(
                        match.id
                    );
                }
            );

            list.appendChild(card);
        }
    );

    updateSelectedMatchCard();
}


function showNoMatches() {

    const list =
        $("matchList");

    if (!list) {
        return;
    }

    list.innerHTML = `

        <div class="players-unavailable">

            <strong>
                No international matches found.
            </strong>

            <br><br>

            There are no matches available
            for ${escapeHtml(currentMonth)}
            from the current Cricket Data sources.

        </div>
    `;
}


function updateSelectedMatchCard() {

    document
        .querySelectorAll(".match-card")
        .forEach(card => {

            card.classList.toggle(
                "active",

                selectedMatch &&
                String(
                    selectedMatch.id
                ) === String(
                    card.dataset.matchId
                )
            );
        });
}


// =========================================================
// SELECT MATCH
// =========================================================

function selectMatch(matchId) {

    const match =
        matches.find(
            item =>
                String(item.id) ===
                String(matchId)
        );

    if (!match) {
        return;
    }

    selectedMatch =
        match;

    updateSelectedMatchCard();

    updateScoreboard(
        match
    );

    resetAiCards();

    loadMatchPlayers(
        match.id
    );
}


// =========================================================
// SCOREBOARD
// =========================================================

function updateScoreboard(match) {

    setText(
        "team1",
        match.team1
    );

    setText(
        "team2",
        match.team2
    );

    setText(
        "score1",
        formatScore(
            match.score1,
            match.wickets1
        )
    );

    setText(
        "score2",
        formatScore(
            match.score2,
            match.wickets2
        )
    );

    setText(
        "overs1",
        formatOvers(
            match.overs1
        )
    );

    setText(
        "overs2",
        formatOvers(
            match.overs2
        )
    );

    setText(
        "matchType",
        match.matchType ||
        "INTERNATIONAL"
    );

    let status =
        "UPCOMING";

    if (match.matchEnded) {
        status = "ENDED";
    } else if (match.matchStarted) {
        status = "LIVE";
    }

    setText(
        "matchStatus",
        match.status ||
        status
    );

    setText(
        "matchBadge",
        status
    );

    const runs =
        (Number(match.score1) || 0) +
        (Number(match.score2) || 0);

    const wickets =
        (Number(match.wickets1) || 0) +
        (Number(match.wickets2) || 0);

    const overs = [
        Number(match.overs1),
        Number(match.overs2)
    ].filter(
        value =>
            !Number.isNaN(value)
    );

    let runRate = "—";

    if (overs.length > 0) {

        const totalOvers =
            overs.reduce(
                (sum, value) =>
                    sum + value,
                0
            );

        if (totalOvers > 0) {

            runRate =
                (
                    runs /
                    totalOvers
                ).toFixed(2);
        }
    }

    setText(
        "runRate",
        runRate
    );

    setText(
        "wickets",
        wickets
    );

    setText(
        "overs",
        overs.length
            ? Math.max(...overs)
            : "—"
    );

    setText(
        "statusShort",
        status
    );
}


// =========================================================
// PLAYER SQUADS
// =========================================================

async function loadMatchPlayers(matchId) {

    const container =
        $("playersContainer") ||
        $("players-list") ||
        $("playersList");

    if (!container) {
        return;
    }

    const cacheKey =
        String(matchId);

    if (squadCache[cacheKey]) {

        renderPlayers(
            squadCache[cacheKey].teams,
            squadCache[cacheKey].source,
            container
        );

        return;
    }

    container.innerHTML = `
        <div class="players-loading">
            Loading player squads...
        </div>
    `;

    try {

        const response =
            await fetch(
                `/api/match-players/${encodeURIComponent(matchId)}`,
                {
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (
            response.ok &&
            data.status === "success" &&
            Array.isArray(data.teams)
        ) {

            squadCache[cacheKey] = {
                teams: data.teams,
                source:
                    data.source ||
                    "Cricket Data"
            };

            renderPlayers(
                data.teams,
                data.source ||
                    "Cricket Data",
                container
            );

            return;
        }

        throw new Error(
            data.message ||
            "Squad information unavailable."
        );

    } catch (error) {

        console.error(
            "Squad error:",
            error
        );

        container.innerHTML = `
            <div class="players-unavailable">
                Squad information unavailable
                for this match.
            </div>
        `;
    }
}


function renderPlayers(teams, source, container) {

    if (
        !Array.isArray(teams) ||
        teams.length === 0
    ) {
        container.innerHTML = `
            <div class="players-unavailable">
                <strong>Players List</strong>
                <br><br>
                Player information is not available for this match.
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="players-title">
            <h2>PLAYERS LIST</h2>
            <span>Source: ${escapeHtml(source || "Cricket Data")}</span>
        </div>

        ${teams.map(team => {

            const players =
                Array.isArray(team.players)
                    ? team.players
                    : [];

            if (players.length === 0) {
                return "";
            }

            return `
                <section class="team-players">

                    <div class="players-header">
                        <h3>
                            ${escapeHtml(
                                team.name || "Team"
                            )}
                        </h3>

                        <span>
                            ${players.length} players
                        </span>
                    </div>

                    <div class="players-grid">

                        ${players.map(player => `

                            <div class="player-chip">

                                <div class="player-avatar">
                                    ${escapeHtml(
                                        getInitials(
                                            player.name
                                        )
                                    )}
                                </div>

                                <span>
                                    ${escapeHtml(
                                        player.name
                                    )}
                                </span>

                            </div>

                        `).join("")}

                    </div>

                </section>
            `;

        }).join("")}
    `;
}

// =========================================================
// AI CARDS
// =========================================================

function resetAiCards() {

    setText(
        "turning-point",
        "Click 'Analyze Match' to generate AI analysis."
    );

    setText(
        "commentary",
        "Click 'Generate Commentary' to create AI commentary."
    );

    currentCommentary = "";
}


async function analyzeMatch() {

    if (!selectedMatch) {

        alert(
            "Please select a match first."
        );

        return;
    }

    setText(
        "turning-point",
        "Sports IQ is analyzing..."
    );

    try {

        const response =
            await fetch(
                `/api/analyze/${encodeURIComponent(selectedMatch.id)}`,
                {
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Analysis failed."
            );
        }

        setText(
            "turning-point",
            data.analysis
        );

    } catch (error) {

        console.error(error);

        setText(
            "turning-point",
            "Could not generate analysis."
        );
    }
}


// =========================================================
// COMMENTARY
// =========================================================

async function generateCommentary() {

    if (!selectedMatch) {

        alert(
            "Please select a match first."
        );

        return;
    }

    setText(
        "commentary",
        "Sports IQ is generating commentary..."
    );

    try {

        const response =
            await fetch(
                `/api/commentary/${encodeURIComponent(selectedMatch.id)}`,
                {
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Commentary failed."
            );
        }

        currentCommentary =
            data.commentary || "";

        setText(
            "commentary",
            currentCommentary
        );

    } catch (error) {

        console.error(error);

        setText(
            "commentary",
            "Could not generate commentary."
        );
    }
}


// =========================================================
// VOICE
// =========================================================

function playCommentary() {

    const text =
        currentCommentary ||
        $("commentary")?.textContent?.trim();

    if (
        !text ||
        text.includes(
            "Click 'Generate Commentary'"
        )
    ) {

        alert(
            "Generate commentary first."
        );

        return;
    }

    if (
        !("speechSynthesis" in window)
    ) {

        alert(
            "Voice playback is not supported."
        );

        return;
    }

    window.speechSynthesis.cancel();

    const utterance =
        new SpeechSynthesisUtterance(
            text
        );

    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;

    window.speechSynthesis.speak(
        utterance
    );
}


// =========================================================
// PLAYER SEARCH
// =========================================================

async function askSportsIQ() {

    const input =
        $("questionInput");

    const answerBox =
        $("answerBox");

    if (!input || !answerBox) {
        return;
    }

    const question =
        input.value.trim();

    if (!question) {

        answerBox.innerHTML = `
            <div class="answer-content">
                Please enter a player name
                or cricket question.
            </div>
        `;

        return;
    }

    answerBox.innerHTML = `
        <div class="thinking">
            Sports IQ is searching...
        </div>
    `;

    try {

        const params =
            new URLSearchParams();

        params.set(
            "question",
            question
        );

        if (selectedMatch) {

            params.set(
                "match_id",
                selectedMatch.id
            );
        }

        const response =
            await fetch(
                `/api/ask?${params.toString()}`,
                {
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (
            data.status !== "success"
        ) {

            throw new Error(
                data.message ||
                "Request failed."
            );
        }

        // IMPORTANT:
        // Player result is rendered separately.
        if (
            data.type === "player" &&
            data.player
        ) {

            showPlayerProfile(
                data.player
            );

            return;
        }

        answerBox.innerHTML = `
            <div class="answer-content">
                ${formatAnswer(
                    data.answer ||
                    "No answer returned."
                )}
            </div>
        `;

    } catch (error) {

        console.error(
            "Player search error:",
            error
        );

        answerBox.innerHTML = `
            <div class="players-unavailable">
                Could not search Sports IQ.
            </div>
        `;
    }
}


// =========================================================
// PLAYER PROFILE
// =========================================================

function showPlayerProfile(player) {

    const answerBox = $("answerBox");

    if (!answerBox) {
        return;
    }

    const name = player.name || "Player";

    const description =
        player.description ||
        "International cricketer";

    const bio =
        player.bio ||
        "Player information is available on Wikipedia.";

    // Works with different possible URL field names
    const wikipediaUrl =
        player.wikipedia_url ||
        player.url ||
        player.wikipedia ||
        `https://en.wikipedia.org/wiki/${encodeURIComponent(
            name.trim().replace(/\s+/g, "_")
        )}`;

    const photo = player.photo
        ? `
            <img
                class="player-photo"
                src="${escapeHtml(player.photo)}"
                alt="${escapeHtml(name)}"
                onerror="this.style.display='none';"
            >
        `
        : `
            <div class="player-placeholder">
                ${escapeHtml(getInitials(name))}
            </div>
        `;

    answerBox.innerHTML = `
        <div class="player-profile">

            <div class="player-image-wrap">
                ${photo}
            </div>

            <div class="player-info">

                <div class="player-label">
                    PLAYER PROFILE
                </div>

                <h3>
                    ${escapeHtml(name)}
                </h3>

                <div class="player-role">
                    ${escapeHtml(description)}
                </div>

                <p class="player-bio">
                    ${escapeHtml(bio)}
                </p>

                <a
                    class="player-link"
                    href="${escapeHtml(wikipediaUrl)}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    📖 View Wikipedia →
                </a>

            </div>

        </div>
    `;
    
}

// =========================================================
// QUESTION ENTER KEY
// =========================================================

function setupQuestionInput() {

    const input =
        $("questionInput");

    if (!input) {
        return;
    }

    input.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                askSportsIQ();
            }
        }
    );
}


// =========================================================
// START
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupMonthSelector();

        setupQuestionInput();

        loadMatches();
    }
);