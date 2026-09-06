document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", (e) => {
        e.preventDefault();
        const target = link.getAttribute("data-target");

        document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
        document.getElementById(target).classList.add("active");

        document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
        link.classList.add("active");
    });
});