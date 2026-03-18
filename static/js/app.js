let intervalo = null;

// 🔥 animación de cambio en KPIs
function animarCambio(id, valor) {
    const el = document.getElementById(id);

    if (el.innerText != valor) {
        el.innerText = valor;

        el.classList.add("kpi-update");

        setTimeout(() => {
            el.classList.remove("kpi-update");
        }, 400);
    }
}

// 📤 subir archivo
async function upload() {
    const file = document.getElementById("fileInput").files[0];

    if (!file) {
        alert("Selecciona un archivo");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    await fetch("/upload", {
        method: "POST",
        body: formData
    });

    alert("Archivo cargado ✅");
}

// 🚀 iniciar proceso
async function start() {
    const res = await fetch("/start", { method: "POST" });
    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    intervalo = setInterval(verEstado, 3000);
}

// 🔄 actualizar dashboard
async function verEstado() {

    const res = await fetch("/status");
    const data = await res.json();

    if (!data.total) return;

    const porcentaje = Math.floor((data.enviados + data.errores) / data.total * 100);

    // 🔥 KPIs animados
    animarCambio("total", data.total);
    animarCambio("enviados", data.enviados);
    animarCambio("errores", data.errores);
    animarCambio("estado", data.estado);

    // 📊 barra
    document.getElementById("barra").style.width = porcentaje + "%";

    // 📋 tabla
    document.getElementById("tabla").innerHTML = `
        <tr>
            <td>${data.proceso_id}</td>
            <td>${data.estado}</td>
            <td>${data.total}</td>
            <td>${data.enviados}</td>
            <td>${data.errores}</td>
        </tr>
    `;

    if (data.estado === "FINALIZADO") {
        clearInterval(intervalo);
    }
}