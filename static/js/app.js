// let intervalo = null;

// // 🔥 animación de cambio en KPIs
// function animarCambio(id, valor) {
//     const el = document.getElementById(id);

//     if (el.innerText != valor) {
//         el.innerText = valor;

//         el.classList.add("kpi-update");

//         setTimeout(() => {
//             el.classList.remove("kpi-update");
//         }, 400);
//     }
// }

// // 📤 subir archivo
// async function upload() {
//     const file = document.getElementById("fileInput").files[0];

//     if (!file) {
//         alert("Selecciona un archivo");
//         return;
//     }

//     const formData = new FormData();
//     formData.append("file", file);

//     await fetch("/upload", {
//         method: "POST",
//         body: formData
//     });

//     alert("Archivo cargado ✅");
// }

// // 🚀 iniciar proceso
// async function start() {
//     const res = await fetch("/start", { method: "POST" });
//     const data = await res.json();

//     if (data.error) {
//         alert(data.error);
//         return;
//     }

//     intervalo = setInterval(verEstado, 3000);
// }

// // 🔄 actualizar dashboard
// async function verEstado() {

//     const res = await fetch("/status");
//     const data = await res.json();

//     if (!data.total) return;

//     const porcentaje = Math.floor((data.enviados + data.errores) / data.total * 100);

//     // 🔥 KPIs animados
//     animarCambio("total", data.total);
//     animarCambio("enviados", data.enviados);
//     animarCambio("errores", data.errores);
//     animarCambio("estado", data.estado);

//     // 📊 barra
//     document.getElementById("barra").style.width = porcentaje + "%";

//     // 📋 tabla
//     document.getElementById("tabla").innerHTML = `
//         <tr>
//             <td>${data.proceso_id}</td>
//             <td>${data.estado}</td>
//             <td>${data.total}</td>
//             <td>${data.enviados}</td>
//             <td>${data.errores}</td>
//         </tr>
//     `;

//     if (data.estado === "FINALIZADO") {
//         clearInterval(intervalo);
//     }
// }



let proceso_id = null;
let interval = null;

// 📤 SUBIR ARCHIVO
async function upload() {
    const fileInput = document.getElementById("fileInput");

    if (!fileInput.files.length) {
        alert("Selecciona un archivo");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const res = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    const data = await res.json();
    alert(data.mensaje);
}


// 🚀 INICIAR PROCESO
async function start() {
    const res = await fetch("/start", {
        method: "POST"
    });

    const data = await res.json();

    if (data.error) {
        alert(data.error);
        return;
    }

    proceso_id = data.proceso_id;

    console.log("Proceso iniciado:", proceso_id);

    // 🔥 empezar polling
    if (interval) clearInterval(interval);

    interval = setInterval(actualizarDashboard, 2000);
}


// 🔄 ACTUALIZAR DASHBOARD
async function actualizarDashboard() {
    if (!proceso_id) return;

    const res = await fetch(`/status/${proceso_id}`);
    const data = await res.json();

    if (!data || Object.keys(data).length === 0) return;

    // KPIs
    document.getElementById("total").innerText = data.total;
    document.getElementById("enviados").innerText = data.enviados;
    document.getElementById("errores").innerText = data.errores;
    document.getElementById("estado").innerText = data.estado;

    // PROGRESO
    let progreso = 0;
    if (data.total > 0) {
        progreso = (data.enviados + data.errores) / data.total * 100;
    }

    document.getElementById("barra").style.width = progreso + "%";

    // TABLA
    const tabla = document.getElementById("tabla");
    tabla.innerHTML = `
        <tr>
            <td>${proceso_id}</td>
            <td>${data.estado}</td>
            <td>${data.total}</td>
            <td>${data.enviados}</td>
            <td>${data.errores}</td>
        </tr>
    `;

    // 🛑 detener cuando termine
    if (data.estado === "FINALIZADO") {
        clearInterval(interval);
    }
}