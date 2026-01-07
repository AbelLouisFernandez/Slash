let movies = [];

function addMovie() {
    const input = document.getElementById("movieInput");
    const name = input.value.trim();

    if (!name || movies.includes(name)) return;


    movies.push(name);
    input.value = "";
    renderMovies();
}

function updateMovie(index, value) {
    movies[index] = value.trim();
}

function removeMovie(index) {
    movies.splice(index, 1);
    renderMovies();
}

function renderMovies() {
    const list = document.getElementById("movieList");
    list.innerHTML = "";

    movies.forEach((movie, index) => {
        const div = document.createElement("div");
        div.className = "movie-item";

        const input = document.createElement("input");
        input.value = movie;
        input.oninput = (e) => updateMovie(index, e.target.value);

        const actions = document.createElement("div");
        actions.className = "actions";

        const removeBtn = document.createElement("button");
        removeBtn.className = "remove-btn";
        removeBtn.textContent = "✕";
        removeBtn.onclick = () => removeMovie(index);

        actions.appendChild(removeBtn);
        div.appendChild(input);
        div.appendChild(actions);
        list.appendChild(div);
    });
}

async function calculate() {
    document.getElementById("plan").innerHTML = "";
    const hoursPerWeek = parseFloat(
        document.getElementById("hoursPerWeek").value
    );

    if (!hoursPerWeek || hoursPerWeek <= 0) {
        alert("Please enter valid hours per week");
        return;
    }


    if (movies.length === 0) {
        alert("Please add at least one movie");
        return;
    }

    const loader = document.getElementById("loader");
    const button = document.getElementById("calcBtn");

    loader.style.display = "block";
    button.disabled = true;
    button.textContent = "Calculating…";

    try {
        const response = await fetch(CALCULATE_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": CSRF_TOKEN
            },
            body: JSON.stringify({
                movies,
                hours_per_week: hoursPerWeek
            })

        });

        const data = await response.json();
        renderPlan(data);

    } catch (err) {
        alert("Something went wrong. Please try again.");
    } finally {
        loader.style.display = "none";
        button.disabled = false;
        button.textContent = "Calculate";
    }
}

function renderPlan(data) {
    const planDiv = document.getElementById("plan");
    planDiv.innerHTML = "";

    const container = document.createElement("div");
    container.className = "plan-container";

    Object.entries(data).forEach(([platform, info]) => {
        const card = document.createElement("div");
        card.className = "plan-card";

        const header = document.createElement("div");
        header.className = "plan-header";

        const name = document.createElement("div");
        name.className = "platform-name";
        name.textContent = platform;

        const price = document.createElement("div");
        price.className = "price";
        if (info.price) {
            price.textContent = `₹${info.price} / month`;
        } else {
            price.textContent = "Price unknown";
            price.classList.add("unknown");
        }

        header.appendChild(name);
        header.appendChild(price);

        card.appendChild(header);

        info.movies.forEach(movie => {
            const m = document.createElement("div");
            m.className = "movie";
            m.textContent = `🎬 ${movie.title} (${movie.hours} hrs)`;
            card.appendChild(m);
        });

        const total = document.createElement("div");
        total.className = "total-time";
        total.textContent = `Total watch time: ${info.total_hours.toFixed(2)} hrs`;

        card.appendChild(total);

        const action = document.createElement("div");
        action.className = "action";
        action.textContent = "Subscribe → Watch → Cancel";

        card.appendChild(action);

        container.appendChild(card);
    });

    planDiv.appendChild(container);
}