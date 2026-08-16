(() => {
  const estado = {
    datos: null,
    vista: "explorar",
    seleccionado: null,
    mapa: null,
    capa: null,
    marcas: [],
    puntoReporte: null,
    marcadorBorrador: null,
    borrador: { descripcion: "", categoria: "", detalle: "", fecha_observacion: "", autor: "" },
    recorte: null,
    capas: { contratos: true, reportes: true, dinero: false },
    filtro: { anio: "", estado: "" },
    zonaDane: null,
    busqueda: null,
    avisoZona: null,
    moderacionToken: "",
    modoModerador: false,
    q: "",
    hilo: null,
    piloto: null,
    escala: null,
    sesion: (crypto.randomUUID && crypto.randomUUID()) || String(Date.now()),
  };

  const $panel = document.getElementById("panel-contenido");
  const categorias = {
    OBRA_INCONCLUSA: "Obra inconclusa",
    OBRA_DETERIORADA: "Obra deteriorada",
    OBRA_NO_VISIBLE: "Obra no visible",
    PROBLEMA_PERSISTENTE: "Problema persistente",
    RIESGO: "Riesgo",
    OTRO: "Otro",
  };
  const estadosContrato = {
    ACTIVO: "Activo",
    FINALIZADO: "Finalizado",
    PROXIMO_A_VENCER: "Próximo a vencer",
    SIN_FECHA_SUFICIENTE: "Sin fecha suficiente",
    DESCONOCIDO: "Desconocido",
  };
  const estadosReporte = {
    BORRADOR: "Borrador",
    PUBLICADO: "Publicado",
    EN_REVISION: "En revisión",
    RELACIONADO: "Con posible conexión",
    VERIFICADO: "Revisada",
    DESCARTADO: "Descartado",
    RETIRADO: "Retirado",
  };
  const estadosOcultos = new Set(["BORRADOR", "DESCARTADO", "RETIRADO"]);

  const escapeHtml = (valor) =>
    String(valor ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

  const ocuparBoton = (boton, texto) => {
    if (!boton) return null;
    const original = boton.textContent;
    boton.disabled = true;
    boton.textContent = texto;
    return original;
  };

  const liberarBoton = (boton, original) => {
    if (!boton) return;
    boton.disabled = false;
    if (original != null) boton.textContent = original;
  };

  const $dialogo = document.getElementById("dialogo-confirmar");
  const confirmarAccion = ({ titulo = "", texto = "", textoConfirmar = "Confirmar", textoCancelar = "Cancelar" } = {}) =>
    new Promise((resolve) => {
      if (!$dialogo || typeof $dialogo.showModal !== "function") {
        resolve(window.confirm(texto));
        return;
      }
      $dialogo.querySelector("#dialogo-titulo").textContent = titulo;
      $dialogo.querySelector("#dialogo-texto").textContent = texto;
      const btnOk = $dialogo.querySelector("#dialogo-confirmar-btn");
      const btnCancelar = $dialogo.querySelector("#dialogo-cancelar");
      btnOk.textContent = textoConfirmar;
      btnCancelar.textContent = textoCancelar;
      const limpiar = () => {
        btnOk.removeEventListener("click", onOk);
        btnCancelar.removeEventListener("click", onCancelar);
        $dialogo.removeEventListener("cancel", onCancelar);
      };
      const onOk = () => {
        limpiar();
        $dialogo.close();
        resolve(true);
      };
      const onCancelar = (ev) => {
        if (ev && ev.preventDefault) ev.preventDefault();
        limpiar();
        $dialogo.close();
        resolve(false);
      };
      btnOk.addEventListener("click", onOk);
      btnCancelar.addEventListener("click", onCancelar);
      $dialogo.addEventListener("cancel", onCancelar);
      $dialogo.showModal();
    });

  const $dialogoMotivo = document.getElementById("dialogo-motivo");
  const pedirMotivo = ({ titulo = "", texto = "", textoOk = "Confirmar" } = {}) =>
    new Promise((resolve) => {
      if (!$dialogoMotivo || typeof $dialogoMotivo.showModal !== "function") {
        const valor = window.prompt(texto || titulo);
        resolve(valor && valor.trim().length >= 10 ? valor.trim() : null);
        return;
      }
      $dialogoMotivo.querySelector("#dialogo-motivo-titulo").textContent = titulo;
      $dialogoMotivo.querySelector("#dialogo-motivo-texto").textContent = texto;
      const campo = $dialogoMotivo.querySelector("#dialogo-motivo-campo");
      campo.value = "";
      const btnOk = $dialogoMotivo.querySelector("#dialogo-motivo-ok");
      const btnCancelar = $dialogoMotivo.querySelector("#dialogo-motivo-cancelar");
      btnOk.textContent = textoOk;
      const limpiar = () => {
        btnOk.removeEventListener("click", onOk);
        btnCancelar.removeEventListener("click", onCancelar);
        $dialogoMotivo.removeEventListener("cancel", onCancelar);
      };
      const onOk = () => {
        const valor = campo.value.trim();
        if (valor.length < 10) {
          campo.focus();
          return;
        }
        limpiar();
        $dialogoMotivo.close();
        resolve(valor);
      };
      const onCancelar = (ev) => {
        if (ev && ev.preventDefault) ev.preventDefault();
        limpiar();
        $dialogoMotivo.close();
        resolve(null);
      };
      btnOk.addEventListener("click", onOk);
      btnCancelar.addEventListener("click", onCancelar);
      $dialogoMotivo.addEventListener("cancel", onCancelar);
      $dialogoMotivo.showModal();
    });

  const plata = (n) => {
    if (n == null) return "cifra no utilizable";
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      maximumFractionDigits: 0,
    }).format(n);
  };

  const daneDe = (feature) => feature.properties.MPIO_CCNCT;
  const municipio = (dane) => estado.datos.municipios[dane];
  const contrato = (id) => estado.datos.contratos[id];
  const reporte = (id) => estado.datos.reportes[id];

  const opcionesMunicipios = (seleccionado) => {
    const lista = Object.values(estado.datos.municipios).sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
    return ['<option value="">Selecciona un municipio…</option>']
      .concat(
        lista.map(
          (m) =>
            `<option value="${escapeHtml(m.dane)}"${m.dane === seleccionado ? " selected" : ""}>${escapeHtml(m.nombre)}</option>`
        )
      )
      .join("");
  };

  const relacionesDe = (tipo, id) =>
    estado.datos.relaciones.filter(
      (rel) =>
        (rel.origen.tipo === tipo && rel.origen.id === id) ||
        (rel.destino.tipo === tipo && rel.destino.id === id)
    );

  const otroDe = (rel, tipo, id) => {
    const yo = rel.origen.tipo === tipo && rel.origen.id === id ? rel.destino : rel.origen;
    return yo;
  };

  const snapDe = (dane) => (estado.recorte && estado.recorte.municipios[dane]) || null;

  const numeroPaso = (clave, alt) => {
    const pasos = (estado.hilo && estado.hilo.pasos) || [];
    const p = pasos.find((x) => x.clave === clave);
    return p ? p.id : alt;
  };

  const hayBorradorConContenido = () => {
    const texto = (estado.borrador.descripcion || "").trim();
    return !!(texto || estado.puntoReporte);
  };

  const vaciarBorrador = () => {
    estado.borrador = { descripcion: "", categoria: "", detalle: "", fecha_observacion: "", autor: "" };
  };

  const TITULOS_SIGUIENTE = {
    zona: "Elige o pregunta por una zona",
    evidencia: "Agrega una observación en esta zona",
    relaciones: "Contrasta con un contrato o espera una sugerencia",
    continuar: "Otra persona puede seguir contrastando aquí",
  };

  const registrarEvento = (accion, objeto, resultado) => {
    fetch("/api/piloto/evento", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        accion,
        sesion: estado.sesion,
        objeto: objeto || {},
        resultado: resultado || "",
      }),
    }).catch(() => {});
  };

  const cargarPiloto = async () => {
    try {
      estado.piloto = await (await fetch("/api/piloto")).json();
    } catch (_err) {
      estado.piloto = null;
    }
  };

  const htmlPiloto = () => {
    const p = estado.piloto;
    if (!p || !p.metricas) return "";
    const t = p.metricas.tiempo_hasta_encontrar_segundos || {};
    const tiempo = t.mediana == null ? "sin muestras" : `${Math.round(t.mediana)} s (mediana, ${t.n})`;
    return `
      <section class="piloto">
        <h2>Qué mide este piloto</h2>
        <p class="muted">${escapeHtml(p.alcance.territorio)} · ${escapeHtml(String(p.alcance.municipios))} municipios · el siguiente paso se nombra, no se enciende.</p>
        <p>${escapeHtml(p.pregunta_central)}</p>
        <p>${escapeHtml(p.lectura)}</p>
        <div class="cifras">
          <div class="cifra"><b>${p.metricas.reportes_creados}</b> reportes creados</div>
          <div class="cifra"><b>${p.metricas.reportes_utiles}</b> reportes útiles</div>
          <div class="cifra"><b>${p.metricas.reportes_duplicados}</b> duplicados</div>
          <div class="cifra"><b>${p.metricas.relaciones_sugeridas}</b> relaciones sugeridas</div>
          <div class="cifra"><b>${p.metricas.relaciones_confirmadas}</b> confirmadas</div>
          <div class="cifra"><b>${p.metricas.contratos_consultados}</b> contratos consultados</div>
          <div class="cifra"><b>${p.metricas.busquedas_realizadas}</b> búsquedas</div>
          <div class="cifra"><b>${escapeHtml(tiempo)}</b> hasta encontrar</div>
        </div>
        <p class="aviso">${escapeHtml(p.nota)}</p>
      </section>
    `;
  };

  const htmlEscala = () => {
    const e = estado.escala;
    if (!e || !e.ejes) return "";
    const ejes = e.ejes
      .map(
        (eje) =>
          `<li><strong>${escapeHtml(eje.id)}</strong> · ahora ${escapeHtml(eje.actual)} (${escapeHtml(eje.valor)}). Siguiente: ${escapeHtml(eje.siguiente)}, sin encender.</li>`
      )
      .join("");
    const puerta = e.puerta || {};
    const criterios = Object.entries(puerta.detalle || {})
      .map(([k, v]) => `<li>${v.ok ? "sí" : "no"} · ${escapeHtml(k)}: ${escapeHtml(v.evidencia)}</li>`)
      .join("");
    return `
      <section class="escala">
        <h2>Hasta dónde se puede crecer</h2>
        <p class="muted">Mapa activo: ${escapeHtml(e.mapa_activo)} · ${escapeHtml(e.territorio_activo)}</p>
        <ul class="filtros">${ejes}</ul>
        <p>${escapeHtml(puerta.regla || "")}</p>
        <ul class="filtros">${criterios}</ul>
        <p>${escapeHtml(puerta.lectura || "")}</p>
        <p class="aviso">${escapeHtml(e.nota || "")}</p>
      </section>
    `;
  };

  const vistaPiloto = () => `
      <p class="kicker">Información interna del piloto</p>
      <h1>Cómo va el piloto y hasta dónde puede crecer</h1>
      <p class="muted">Esto no es una funcionalidad para investigar contratos — es la evaluación interna de si LADERA está funcionando, no cuántas personas la usan.</p>
      <div class="vista-piloto">${htmlPiloto()}${htmlEscala()}</div>
      <p><button type="button" class="tarjeta" data-ir="explorar">Volver a Inicio</button></p>
    `;

  const cargarHilo = async () => {
    const q = new URLSearchParams();
    if (estado.zonaDane) q.set("dane", estado.zonaDane);
    if (estado.filtro.anio) q.set("anio", estado.filtro.anio);
    if (estado.filtro.estado) q.set("estado", estado.filtro.estado);
    if (estado.q) q.set("pregunta", estado.q);
    const res = await fetch(`/api/recorrido?${q.toString()}`);
    estado.hilo = await res.json();
  };

  const centrarZona = (dane) => {
    if (!estado.mapa || !estado.capa || !dane) return;
    estado.capa.eachLayer((layer) => {
      if (daneDe(layer.feature) === dane && layer.getBounds) {
        estado.mapa.fitBounds(layer.getBounds(), { padding: [28, 28], maxZoom: 10 });
      }
    });
  };

  const htmlHilo = () => {
    const h = estado.hilo;
    if (!h) return "";
    const zona = h.zona && h.zona.nombre ? h.zona.nombre : "sin zona";
    const periodo = h.filtro && h.filtro.anio ? h.filtro.anio : "todos los años";
    const pregunta = h.pregunta ? ` · «${h.pregunta}»` : "";
    const pasos = (h.pasos || [])
      .map(
        (p) =>
          `<li class="${p.listo ? "listo" : ""} ${p.clave === h.siguiente ? "aqui" : ""}">${escapeHtml(p.id)}. ${escapeHtml(p.titulo)}</li>`
      )
      .join("");
    return `
      <nav class="hilo" aria-label="Recorrido de contraste">
        <p class="hilo-zona">${escapeHtml(zona)} · ${escapeHtml(String(periodo))}${escapeHtml(pregunta)}</p>
        <ol>${pasos}</ol>
        <p class="muted">${escapeHtml(TITULOS_SIGUIENTE[h.siguiente] || "")}</p>
      </nav>
    `;
  };

  const colorDinero = (plata, max) => {
    if (!plata || !max) return "#d9d2c4";
    // Escala logarítmica: con datos reales, un municipio con mucha más plata que
    // el resto dejaba a todos los demás casi del mismo tono con una escala lineal.
    const t = Math.min(1, Math.log1p(plata) / Math.log1p(max));
    const r = Math.round(217 + (63 - 217) * t);
    const g = Math.round(210 + (107 - 210) * t);
    const b = Math.round(196 + (82 - 196) * t);
    return `rgb(${r}, ${g}, ${b})`;
  };

  const estilo = (feature, seleccionado) => {
    const dane = daneDe(feature);
    const snap = snapDe(dane);
    const capas = estado.capas;
    const tieneC = capas.contratos && snap && snap.contratos > 0;
    const tieneR = capas.reportes && snap && snap.reportes > 0;
    let fill = "#d9d2c4";
    let color = "#6a6256";
    let weight = 1;
    if (capas.dinero && snap && snap.plata > 0) {
      fill = colorDinero(snap.plata, estado.recorte.plata_max);
      color = "#2a4032";
      if (tieneR) {
        color = "#b5523a";
        weight = 2;
      }
    } else if (tieneC && tieneR) {
      fill = "#4a5e48";
      color = "#b5523a";
      weight = 2;
    } else if (tieneC) {
      fill = "#3f6b52";
      color = "#2a4032";
    } else if (tieneR) {
      fill = "#e4d8c6";
      color = "#b5523a";
      weight = 2;
    }
    if (seleccionado) {
      color = "#c4a35a";
      weight = 3;
    }
    return { fillColor: fill, color, weight, fillOpacity: 0.86 };
  };

  const pintarCapa = () => {
    if (!estado.capa) return;
    const daneSel =
      estado.seleccionado && estado.seleccionado.tipo === "municipio"
        ? estado.seleccionado.id
        : estado.seleccionado && estado.seleccionado.tipo === "contrato"
          ? contrato(estado.seleccionado.id)?.municipio_dane
          : estado.seleccionado && estado.seleccionado.tipo === "reporte"
            ? reporte(estado.seleccionado.id)?.ubicacion.dane
            : null;
    estado.capa.setStyle((f) => estilo(f, daneDe(f) === daneSel));
    pintarLeyenda();
  };

  const limpiarMarcas = () => {
    estado.marcas.forEach((m) => m.remove());
    estado.marcas = [];
  };

  const idsReporteRecorte = () => {
    const ids = new Set();
    if (!estado.recorte) return ids;
    Object.values(estado.recorte.municipios).forEach((m) => {
      (m.reporte_ids || []).forEach((id) => ids.add(id));
    });
    return ids;
  };

  const pintarLeyenda = () => {
    const caja = document.getElementById("mapa-leyenda");
    if (!caja) return;
    const chips = ['<span class="chip chip-vacio">sin dato</span>'];
    if (estado.capas.contratos) chips.push('<span class="chip chip-contrato">contratos</span>');
    if (estado.capas.reportes) chips.push('<span class="chip chip-reporte">reportes</span>');
    if (estado.capas.contratos && estado.capas.reportes) chips.push('<span class="chip chip-ambos">ambos</span>');
    caja.innerHTML = chips.join("");
    if (estado.capas.dinero) {
      caja.insertAdjacentHTML(
        "beforeend",
        `<span class="chip chip-degradado">
           <strong>Contratación acumulada</strong>
           <span class="degradado-dinero" aria-hidden="true"></span>
           <span>menor · mayor</span>
         </span>`
      );
    }
  };

  const pintarPieFuente = () => {
    const p = document.getElementById("pie-fuente");
    if (!p || !estado.datos) return;
    const esFixture = estado.datos.resumen.fuente === "fixture";
    p.textContent = esFixture
      ? "Datos de demostración."
      : "Datos de contratación provenientes del conjunto procesado de SECOP II.";
  };

  const marcarPuntos = () => {
    limpiarMarcas();
    if (!estado.mapa || !estado.datos || !estado.capas.reportes) return;
    const permitidos = idsReporteRecorte();
    Object.values(estado.datos.reportes).forEach((rep) => {
      if (estado.recorte && !permitidos.has(rep.id)) return;
      const { lat, lng } = rep.ubicacion;
      if (lat == null || lng == null) return;
      const marca = L.circleMarker([lat, lng], {
        radius: 7,
        color: "#221e18",
        weight: 1,
        fillColor: "#b5523a",
        fillOpacity: 0.95,
      }).addTo(estado.mapa);
      marca.bindTooltip(rep.ubicacion.detalle || rep.ubicacion.nombre);
      marca.on("click", () => abrir({ tipo: "reporte", id: rep.id }));
      estado.marcas.push(marca);
    });
  };

  const marcarNav = () => {
    document.querySelectorAll(".nav button").forEach((b) => {
      const activo = b.dataset.vista === estado.vista;
      b.classList.toggle("esta", activo);
      if (activo) b.setAttribute("aria-current", "page");
      else b.removeAttribute("aria-current");
    });
  };

  const abrir = (sel) => {
    estado.seleccionado = sel;
    if (sel && sel.tipo === "municipio") {
      estado.zonaDane = sel.id;
      centrarZona(sel.id);
    } else if (sel && sel.tipo === "contrato") {
      const c = contrato(sel.id);
      if (c) estado.zonaDane = c.municipio_dane;
    } else if (sel && sel.tipo === "reporte") {
      const r = reporte(sel.id);
      if (r) estado.zonaDane = r.ubicacion.dane;
    }
    if (sel) estado.vista = "mapa";
    if (sel && sel.tipo === "municipio") registrarEvento("ABRIR_ZONA", { tipo: "municipio", id: sel.id });
    if (sel && (sel.tipo === "contrato" || sel.tipo === "reporte")) {
      registrarEvento("CONSULTAR", { tipo: sel.tipo, id: sel.id });
    }
    pintarCapa();
    marcarNav();
    cargarHilo().then(renderPanel);
  };

  const quitarMarcadorBorrador = () => {
    if (estado.marcadorBorrador) {
      estado.marcadorBorrador.remove();
      estado.marcadorBorrador = null;
    }
    estado.puntoReporte = null;
  };

  const textoPunto = (punto, error) => {
    if (error) return error;
    if (!punto || !punto.dane) return "Haz clic en el mapa y arrastra el marcador para ajustar.";
    return `Municipio: ${punto.nombre}. Puedes arrastrar el punto.`;
  };

  const pintarCamposPunto = (error) => {
    const estadoPunto = document.getElementById("punto-estado");
    const lat = document.getElementById("campo-lat");
    const lng = document.getElementById("campo-lng");
    if (lat) lat.value = estado.puntoReporte ? estado.puntoReporte.lat : "";
    if (lng) lng.value = estado.puntoReporte ? estado.puntoReporte.lng : "";
    if (estadoPunto) estadoPunto.textContent = textoPunto(estado.puntoReporte, error);
  };

  const ponerPuntoReporte = async (latlng, danePreferido) => {
    if (!estado.mapa) return;
    if (estado.marcadorBorrador) {
      estado.marcadorBorrador.setLatLng(latlng);
    } else {
      estado.marcadorBorrador = L.marker(latlng, { draggable: true, autoPan: true }).addTo(estado.mapa);
      estado.marcadorBorrador.on("dragend", (ev) => ponerPuntoReporte(ev.target.getLatLng()));
    }
    estado.puntoReporte = { lat: latlng.lat, lng: latlng.lng, dane: "", nombre: "" };
    pintarCamposPunto(null);
    try {
      const params = new URLSearchParams({ lat: String(latlng.lat), lng: String(latlng.lng) });
      if (danePreferido) params.set("dane", danePreferido);
      const res = await fetch(`/api/territorio?${params.toString()}`);
      const data = await res.json();
      if (!res.ok) {
        estado.puntoReporte.dane = "";
        pintarCamposPunto(data.error || "El punto no está en Antioquia.");
        return;
      }
      estado.puntoReporte.dane = data.dane;
      estado.puntoReporte.nombre = data.nombre;
      pintarCamposPunto(null);
    } catch (err) {
      pintarCamposPunto(err.message);
    }
  };

  const irVista = async (vista) => {
    if (estado.vista === "reportar" && vista !== "reportar") {
      if (hayBorradorConContenido()) {
        const salir = await confirmarAccion({
          titulo: "Observación sin enviar",
          texto: "Tienes una observación sin enviar. Si sales ahora se pierde lo escrito.",
          textoConfirmar: "Salir sin guardar",
          textoCancelar: "Seguir editando",
        });
        if (!salir) return;
      }
      quitarMarcadorBorrador();
      vaciarBorrador();
    }
    estado.vista = vista;
    if (vista === "mapa" && estado.zonaDane) {
      estado.seleccionado = { tipo: "municipio", id: estado.zonaDane };
      centrarZona(estado.zonaDane);
    }
    pintarCapa();
    marcarNav();
    await cargarHilo();
    renderPanel();
    if (vista === "buscar") {
      const q = document.getElementById("q");
      if (q) q.focus();
    }
  };

  const tarjetaContrato = (c) => `
    <li>
      <button type="button" class="tarjeta" data-abrir="contrato:${escapeHtml(c.id)}">
        <strong>${escapeHtml(c.id)}</strong> · ${escapeHtml(estadosContrato[c.estado] || c.estado)}
        <small>${escapeHtml(c.objeto)}</small>
        <small>${plata(c.valor)}</small>
      </button>
    </li>`;

  const SENAL_ETIQUETA = {
    TERRITORIAL: "Mismo municipio",
    TEMPORAL: "Periodo relacionado",
    SEMANTICA: "Tema similar",
  };

  const etiquetaRelacion = (rel) => {
    if (rel.estado === "CONFIRMADA") return "Conexión confirmada";
    if (rel.estado === "SUGERIDA") return "Posible conexión";
    return "Conexión descartada";
  };

  const CONEXION_SIGNIFICADO = {
    SUGERIDA: "LADERA detectó señales que justifican revisar esta conexión. No es una relación comprobada.",
    CONFIRMADA: "Una persona autorizada revisó y confirmó esta conexión.",
    DESCARTADA: "Una persona autorizada revisó esta posible conexión y la descartó.",
  };

  const explicacionConexion = (rel) => {
    const items = (rel.senales || []).map((s) => `<li>✓ ${escapeHtml(SENAL_ETIQUETA[s] || s)}</li>`).join("");
    return `
      <div class="conexion-porque">
        <p class="muted">${escapeHtml(CONEXION_SIGNIFICADO[rel.estado] || "")}</p>
        <p class="muted">¿Por qué LADERA propone esta conexión?</p>
        ${items ? `<ul class="lista-senales">${items}</ul>` : ""}
        <p class="muted">${escapeHtml(rel.evidencia)}</p>
      </div>
    `;
  };

  const accionesRelacion = (rel) => {
    if (rel.estado !== "SUGERIDA") return "";
    return `
      <p class="acciones-rel">
        <button type="button" class="secundario" data-revisar="${escapeHtml(rel.id)}:CONFIRMADA">Confirmar conexión</button>
        <button type="button" class="secundario" data-revisar="${escapeHtml(rel.id)}:DESCARTADA">Descartar</button>
      </p>`;
  };

  const tarjetaReporte = (r) => `
    <li>
      <button type="button" class="tarjeta" data-abrir="reporte:${escapeHtml(r.id)}">
        <strong>${escapeHtml(categorias[r.categoria] || r.categoria)}</strong>
        <small>${escapeHtml(estadosReporte[r.estado] || r.estado)} · ${escapeHtml(r.descripcion)}</small>
        <small>${escapeHtml(r.ubicacion.nombre)}${r.ubicacion.detalle ? " · " + escapeHtml(r.ubicacion.detalle) : ""}</small>
      </button>
    </li>`;

  const vistaExplorar = () => {
    const r = estado.datos.resumen;
    const esFixture = r.fuente === "fixture";
    const excluidos = r.contratos_fuera_del_mapa;
    return `
      ${htmlHilo()}
      <p class="kicker">Un solo recorrido</p>
      <h1>De lo observado a la evidencia pública</h1>
      <p class="muted">
        Pregunta, elige una zona o marca un punto. El mapa, los contratos y los
        reportes son el mismo hilo: territorio, periodo, observación y fuente.
      </p>
      <div class="cifras">
        <div class="cifra"><b>${r.municipios}</b> municipios</div>
        <div class="cifra"><b>${r.contratos}</b> contratos${esFixture ? " (fixture)" : " (SECOP II)"}</div>
        <div class="cifra"><b>${r.reportes}</b> reportes</div>
      </div>
      ${
        excluidos && excluidos.total > 0
          ? `<p class="aviso">${excluidos.total} contratos no se muestran en el mapa porque el registro no permite asignarlos responsablemente a un único municipio (varios municipios mencionados a la vez, ambiguos, o sin dato territorial suficiente). No se les asigna un municipio al azar.</p>`
          : ""
      }
      ${
        esFixture
          ? `
      <h2>Tres hilos del fixture</h2>
      <ul class="lista">
        <li><button type="button" class="tarjeta" data-recorrido="05001" data-anio="2026" data-pregunta="muro inconcluso en El Popular">El Popular, Medellín — contrato, valor, reporte y una posible relación</button></li>
        <li><button type="button" class="tarjeta" data-recorrido="05088">Bello — hay contratación identificada y nadie ha observado todavía</button></li>
        <li><button type="button" class="tarjeta" data-recorrido="05361">Ituango — hay un reporte y no hay posible conexión conocida</button></li>
      </ul>`
          : ""
      }
      <p class="aviso">${escapeHtml(r.nota)}</p>
      ${
        estado.modoModerador
          ? `<h2>Vista de moderador</h2><p class="muted">Solo visible en este navegador porque activaste el PIN de moderador.</p>${listaConfianza()}`
          : ""
      }
    `;
  };

  const listaConfianza = () => {
    const todos = Object.values(estado.datos.reportes || {});
    const revision = todos.filter((rep) => rep.estado === "EN_REVISION");
    const ocultos = todos.filter((rep) => estadosOcultos.has(rep.estado));
    const bloque = (titulo, filas, vacio) => `
      <h2>${titulo}</h2>
      ${filas.length ? `<ul class="lista">${filas.map(tarjetaReporte).join("")}</ul>` : `<p class="muted">${vacio}</p>`}
    `;
    return `
      ${bloque("En revisión", revision, "No hay observaciones esperando revisión en este equipo.")}
      ${ocultos.length ? bloque("Fuera de la superficie pública", ocultos, "") : ""}
    `;
  };

  const vistaMunicipio = (dane) => {
    const mun = municipio(dane);
    if (!mun) return `<p>Municipio no encontrado.</p>`;
    const snap = snapDe(dane) || mun;
    const contratos = (snap.contrato_ids || mun.contrato_ids).map(contrato).filter(Boolean);
    const reportes = (snap.reporte_ids || mun.reporte_ids).map(reporte).filter(Boolean);
    const periodo = estado.filtro.anio ? ` · ${escapeHtml(estado.filtro.anio)}` : "";
    const relsZona = (estado.datos.relaciones || []).filter((rel) => {
      if (rel.estado === "DESCARTADA") return false;
      const ids = [rel.origen, rel.destino];
      return ids.some(
        (e) =>
          (e.tipo === "contrato" && contratos.some((c) => c.id === e.id)) ||
          (e.tipo === "reporte" && reportes.some((r) => r.id === e.id))
      );
    });
    return `
      ${htmlHilo()}
      <p class="kicker">Zona · ${escapeHtml(mun.dane)}${periodo}</p>
      <h1>${escapeHtml(mun.nombre)}</h1>
      <div class="cifras">
        <div class="cifra"><b>${plata(snap.plata != null ? snap.plata : mun.plata_total)}</b> contratación acumulada</div>
        <div class="cifra"><b>${snap.contratos != null ? snap.contratos : mun.contratos}</b> contratos identificados</div>
        <div class="cifra"><b>${snap.finalizados || 0}</b> finalizados</div>
        <div class="cifra"><b>${snap.activos || 0}</b> activos</div>
        <div class="cifra"><b>${snap.reportes != null ? snap.reportes : mun.reportes}</b> reportes ciudadanos</div>
        <div class="cifra"><b>${snap.contratos_relacionados || 0}</b> con conexión confirmada</div>
        <div class="cifra"><b>${snap.relaciones_sugeridas || 0}</b> posibles conexiones</div>
        <div class="cifra"><b>${snap.sin_cifra || 0}</b> sin cifra usable</div>
      </div>
      ${(snap.sin_cifra || 0) > 0 ? `<p class="muted">Algunos valores no pudieron utilizarse para el cálculo.</p>` : ""}
      <p class="aviso">${escapeHtml((estado.recorte && estado.recorte.nota) || "Cero contratos identificados no significa cero inversión.")}</p>
      <h2>${numeroPaso("contratos", 3)}. Contratos en esta zona</h2>
      ${contratos.length ? `<ul class="lista">${contratos.map(tarjetaContrato).join("")}</ul>` : `<p class="muted">Sin contratación identificada en el conjunto analizado. Eso no significa cero inversión.</p>`}
      <h2>${numeroPaso("reportes", 5)}. Reportes existentes</h2>
      ${reportes.length ? `<ul class="lista">${reportes.map(tarjetaReporte).join("")}</ul>` : `<p class="muted">Nadie ha publicado un reporte en este municipio todavía.</p>`}
      <p><button type="button" class="tarjeta" data-ir="reportar">${numeroPaso("evidencia", 6)}. Agregar una observación en ${escapeHtml(mun.nombre)}</button></p>
      <h2>${numeroPaso("relaciones", 7)}. Posibles conexiones</h2>
      ${
        relsZona.length
          ? relsZona
              .map((rel) => {
                const cid = rel.origen.tipo === "contrato" ? rel.origen.id : rel.destino.id;
                const rid = rel.origen.tipo === "reporte" ? rel.origen.id : rel.destino.id;
                return `<p><span class="estado ${rel.estado.toLowerCase()}">${escapeHtml(etiquetaRelacion(rel))}</span></p>
                  ${explicacionConexion(rel)}
                  <ul class="lista">${contrato(cid) ? tarjetaContrato(contrato(cid)) : ""}${reporte(rid) ? tarjetaReporte(reporte(rid)) : ""}</ul>
                  ${accionesRelacion(rel)}`;
              })
              .join("")
          : `<p class="muted">Aún no hay una posible conexión registrada. Al agregar evidencia, la plataforma puede sugerir una. Eso no confirma el reporte.</p>`
      }
      <p class="aviso">${numeroPaso("continuar", 8)}. Otra persona puede preguntar de nuevo, señalar un reporte o confirmar una posible conexión desde esta misma zona.</p>
    `;
  };

  const vistaContrato = (id) => {
    const c = contrato(id);
    if (!c) return `<p>Contrato no encontrado.</p>`;
    const rels = relacionesDe("contrato", id);
    const reportes = rels
      .map((rel) => {
        const otro = otroDe(rel, "contrato", id);
        return otro.tipo === "reporte" ? { rel, rep: reporte(otro.id) } : null;
      })
      .filter((x) => x && x.rep);
    const fuente = c.url_fuente
      ? `<p><a class="enlace" href="${escapeHtml(c.url_fuente)}" target="_blank" rel="noopener">Abrir expediente en SECOP</a></p>
         <p class="muted">El enlace sale del campo URLProceso.${c.fuente === "fixture" ? " Este contrato es un dato de demostración, no uno real." : ""}</p>`
      : `<p class="muted">Este registro no trae URLProceso.</p>`;
    const lugares = (c.ubicaciones || [])
      .map((u) => `<li><strong>${escapeHtml(u.nombre)}</strong><small>Fragmento: “${escapeHtml(u.fragmento)}”</small></li>`)
      .join("");
    return `
      ${htmlHilo()}
      <p class="kicker">Contrato · ${escapeHtml(c.fuente)}</p>
      <h1>${escapeHtml(c.id)}</h1>
      <p><span class="estado">${escapeHtml(estadosContrato[c.estado] || c.estado)}</span></p>
      <p>${escapeHtml(c.objeto)}</p>
      <p class="muted">${escapeHtml(c.entidad)} · ${escapeHtml(c.municipio_nombre)}</p>
      <p>${plata(c.valor)}${c.valor_motivo ? ` <span class="muted">(${escapeHtml(c.valor_motivo)})</span>` : ""}</p>
      <p class="muted">${escapeHtml(c.fecha_inicio || "sin inicio")} → ${escapeHtml(c.fecha_fin || "sin fin")}</p>
      ${fuente}
      ${bloqueProcedencia(c)}
      ${lugares ? `<h2>Lugares con fragmento</h2><ul class="lista">${lugares}</ul>` : ""}
      <p><button type="button" class="tarjeta" data-abrir="municipio:${escapeHtml(c.municipio_dane)}">Volver a la zona ${escapeHtml(c.municipio_nombre)}</button></p>
      <h2>Reportes en contraste</h2>
      ${
        reportes.filter(({ rel }) => rel.estado !== "DESCARTADA").length
          ? reportes
              .filter(({ rel }) => rel.estado !== "DESCARTADA")
              .map(
                ({ rel, rep }) => `
            <p><span class="estado ${rel.estado.toLowerCase()}">${escapeHtml(etiquetaRelacion(rel))}</span></p>
            ${explicacionConexion(rel)}
            <ul class="lista">${tarjetaReporte(rep)}</ul>
            ${accionesRelacion(rel)}`
              )
              .join("")
          : `<p class="muted">No hay una posible conexión registrada con reportes.</p>`
      }
    `;
  };

  const vistaReporte = (id) => {
    const r = reporte(id);
    if (!r) return `<p>Reporte no encontrado.</p>`;
    const rels = relacionesDe("reporte", id);
    const contratos = rels
      .map((rel) => {
        const otro = otroDe(rel, "reporte", id);
        return otro.tipo === "contrato" ? { rel, con: contrato(otro.id) } : null;
      })
      .filter((x) => x && x.con);
    const ev = (r.evidencias || [])
      .map(
        (e) => `
        <figure class="evidencia">
          <img src="${escapeHtml(e.url)}" alt="Evidencia ${escapeHtml(e.id)}">
          <figcaption class="muted">${escapeHtml(e.metadata?.nota || e.tipo)}</figcaption>
        </figure>`
      )
      .join("");
    return `
      ${htmlHilo()}
      <p class="kicker">Reporte · ${escapeHtml(estadosReporte[r.estado] || r.estado)}</p>
      <h1>${escapeHtml(categorias[r.categoria] || r.categoria)}</h1>
      <p>${escapeHtml(r.descripcion)}</p>
      <p class="muted">
        Observado el ${escapeHtml(r.fecha_observacion)} ·
        registrado el ${escapeHtml((r.fecha_creacion || "").slice(0, 10))} ·
        ${escapeHtml(r.ubicacion.nombre)}
        ${r.ubicacion.detalle ? " · " + escapeHtml(r.ubicacion.detalle) : ""}
      </p>
      <p class="muted">Autor: ${escapeHtml(r.autor)}. Esto es una observación, no un hecho verificado.</p>
      ${bloqueConfianza(r)}
      ${ev || `<p class="muted">Sin evidencia fotográfica.</p>`}
      <p><button type="button" class="tarjeta" data-abrir="municipio:${escapeHtml(r.ubicacion.dane)}">Volver a la zona ${escapeHtml(r.ubicacion.nombre)}</button></p>
      <h2>Contraste con contratación</h2>
      ${
        contratos.filter(({ rel }) => rel.estado !== "DESCARTADA").length
          ? contratos
              .filter(({ rel }) => rel.estado !== "DESCARTADA")
              .map(
                ({ rel, con }) => `
            <p><span class="estado ${rel.estado.toLowerCase()}">${escapeHtml(etiquetaRelacion(rel))}</span></p>
            ${explicacionConexion(rel)}
            <ul class="lista">${tarjetaContrato(con)}</ul>
            ${accionesRelacion(rel)}`
              )
              .join("")
          : `<p class="muted">No hay una posible conexión con contratación para este reporte.</p>`
      }
      <form class="reporte" id="form-directa">
        <p class="paso">Si conoces el contrato</p>
        <p class="muted">Indicar un contrato no prueba que la obra se haya ejecutado.</p>
        <label>Contrato
          <select name="contrato_id" required>${
            Object.values(estado.datos.contratos)
              .sort((a, b) => {
                const da = a.municipio_dane === r.ubicacion.dane ? 0 : 1;
                const db = b.municipio_dane === r.ubicacion.dane ? 0 : 1;
                return da - db || a.id.localeCompare(b.id);
              })
              .map((c) => `<option value="${escapeHtml(c.id)}">${escapeHtml(c.id)} · ${escapeHtml(c.municipio_nombre)}</option>`)
              .join("")
          }</select>
        </label>
        <button type="submit">Indicar este contrato</button>
      </form>
      ${formulariosConfianza(r)}
    `;
  };

  const VALOR_CLASE_TEXTO = {
    UTILIZABLE: "La cifra viene tal como está en el registro público.",
    NO_UTILIZABLE: "La cifra no se pudo usar tal como llegó — no se reemplazó por una estimación.",
    REVISAR: "La cifra quedó marcada para revisar a mano; no se usó sin más.",
  };
  const RESOLUCION_TEXTO = {
    OBJETO: "El municipio se identificó porque el texto del contrato lo menciona explícitamente.",
    CIUDAD_ENTIDAD: "El municipio salió del campo de ciudad del registro, no del texto del contrato.",
    MULTIMUNICIPIO: "El texto del contrato menciona más de un municipio a la vez.",
    AMBIGUO: "El nombre de la ciudad coincide con más de un municipio; no se eligió uno al azar.",
    SIN_RESOLVER: "No fue posible identificar un municipio único con la información disponible.",
  };

  const bloqueProcedencia = (c) => {
    const partes = [];
    if (c.valor_clase) partes.push(VALOR_CLASE_TEXTO[c.valor_clase] || c.valor_clase);
    if (c.resolucion_territorial) partes.push(RESOLUCION_TEXTO[c.resolucion_territorial] || c.resolucion_territorial);
    if (!partes.length) return "";
    return `
      <section class="confianza">
        <h2>Procedencia de la cifra y el territorio</h2>
        ${partes.map((p) => `<p class="muted">${escapeHtml(p)}</p>`).join("")}
      </section>
    `;
  };

  const bloqueConfianza = (r) => {
    const c = r.confianza || {};
    const ultima = c.ultima
      ? `${c.ultima.accion} · ${c.ultima.actor} · ${String(c.ultima.fecha || "").slice(0, 10)} → ${c.ultima.resultado}`
      : "Sin decisiones posteriores al estado inicial.";
    return `
      <section class="confianza">
        <h2>¿Por qué este estado?</h2>
        <p>${escapeHtml(c.explicacion || "Aún no hay una explicación registrada.")}</p>
        <p class="muted">${escapeHtml(ultima)}</p>
        ${c.senalamientos ? `<p class="muted">Señalamientos: ${escapeHtml(c.senalamientos)}</p>` : ""}
      </section>
    `;
  };

  const formulariosConfianza = (r) => {
    const destinos = ["EN_REVISION", "PUBLICADO", "RELACIONADO", "VERIFICADO", "DESCARTADO", "RETIRADO"]
      .filter((s) => s !== r.estado)
      .map((s) => `<option value="${s}">${escapeHtml(estadosReporte[s])}</option>`)
      .join("");
    const senalar = estadosOcultos.has(r.estado)
      ? ""
      : `
      <form class="reporte" id="form-senalar">
        <p class="paso">Señalar contenido</p>
        <p class="muted">No descarta el reporte. Si se acumulan señalamientos, vuelve a revisión.</p>
        <label>Motivo
          <textarea name="motivo" required minlength="10" maxlength="400" placeholder="¿Por qué este contenido no debería estar a la vista?"></textarea>
        </label>
        <button type="submit">Señalar</button>
      </form>`;
    const retirar = r.estado === "RETIRADO" || r.estado === "DESCARTADO"
      ? ""
      : `
      <form class="reporte" id="form-retirar">
        <p class="paso">Retirar</p>
        <label>Motivo
          <textarea name="motivo" required minlength="10" maxlength="400" placeholder="Por qué se retira de la superficie pública"></textarea>
        </label>
        <button type="submit">Retirar observación</button>
      </form>`;
    return `
      ${senalar}
      <form class="reporte" id="form-revisar-reporte">
        <p class="paso">Revisión local</p>
        <p class="muted">Verificar no declara irregularidad ni da el reporte por verdadero. La IA no puede verificar.</p>
        <label>Nuevo estado
          <select name="estado" required>${destinos}</select>
        </label>
        <label>Motivo de la decisión
          <textarea name="motivo" required minlength="10" maxlength="400" placeholder="Queda en la bitácora. Es la respuesta a por qué tiene este estado."></textarea>
        </label>
        <label>Quién decide (opcional)
          <input name="actor" maxlength="80" placeholder="moderación local">
        </label>
        <button type="submit">Registrar decisión</button>
      </form>
      ${retirar}
    `;
  };

  const vistaReportar = () => {
    const b = estado.borrador;
    const cats = Object.entries(categorias)
      .map(([k, v]) => `<option value="${k}"${k === b.categoria ? " selected" : ""}>${escapeHtml(v)}</option>`)
      .join("");
    const punto = estado.puntoReporte || {};
    const zona = estado.zonaDane ? municipio(estado.zonaDane) : null;
    return `
      ${htmlHilo()}
      <p class="kicker">${numeroPaso("evidencia", 6)}. Agregar evidencia</p>
      <h1>${zona ? `Observar en ${escapeHtml(zona.nombre)}` : "Nueva observación"}</h1>
      <p class="muted">${zona ? `Sigues en ${escapeHtml(zona.nombre)}. ` : ""}No necesitas conocer un contrato. Describe lo que observaste, márcalo en el mapa y, si puedes, adjunta una foto.</p>
      <div class="zona-elegir">
        <label>Municipio (ubica el mapa; el punto exacto se marca haciendo clic o arrastrando)
          <select id="select-municipio-reportar" class="selector-municipio">${opcionesMunicipios(estado.zonaDane || "")}</select>
        </label>
      </div>
      <form class="reporte" id="form-reporte">
        <p class="paso">Qué observaste</p>
        <label>Descripción
          <textarea name="descripcion" required maxlength="1200" placeholder="¿Qué viste en el territorio?">${escapeHtml(b.descripcion || "")}</textarea>
        </label>
        <label>Categoría
          <select name="categoria" required>${cats}</select>
        </label>
        <p class="paso">Dónde</p>
        <p class="punto-estado" id="punto-estado">${escapeHtml(textoPunto(estado.puntoReporte))}</p>
        <input type="hidden" name="lat" id="campo-lat" value="${punto.lat != null ? escapeHtml(punto.lat) : ""}">
        <input type="hidden" name="lng" id="campo-lng" value="${punto.lng != null ? escapeHtml(punto.lng) : ""}">
        <label>Lugar más específico (opcional)
          <input name="detalle" maxlength="160" placeholder="barrio, vereda, vía" value="${escapeHtml(b.detalle || "")}">
        </label>
        <p class="paso">Cuándo lo observaste</p>
        <label>Fecha de la observación
          <input name="fecha_observacion" type="date" required value="${escapeHtml(b.fecha_observacion || "")}">
        </label>
        <p class="muted">La fecha en que envías el reporte la registra el sistema.</p>
        <p class="paso">Evidencia</p>
        <label>Fotografía (opcional)
          <input name="foto" type="file" accept="image/jpeg,image/png,image/webp,image/gif">
        </label>
        <label>Tu nombre o seudónimo (opcional)
          <input name="autor" maxlength="80" value="${escapeHtml(b.autor || "")}">
        </label>
        <button type="submit">Enviar observación</button>
      </form>
      <p class="aviso">Queda en revisión en este equipo. No es un hecho verificado y no se vincula solo a un contrato.</p>
    `;
  };

  const ESTADO_FRASE = {
    ACTIVO: "Contratos activos",
    FINALIZADO: "Contratos finalizados",
    PROXIMO_A_VENCER: "Contratos próximos a vencer",
    SIN_FECHA_SUFICIENTE: "Sin fecha suficiente para saber el estado",
    DESCONOCIDO: "Estado del contrato desconocido",
  };

  const textoPeriodo = (periodo) => {
    const desde = (periodo.desde || "").slice(0, 4);
    const hasta = (periodo.hasta || "").slice(0, 4);
    if (desde && desde === hasta) return desde;
    if (desde && hasta) return `${desde} → ${hasta}`;
    return desde || hasta || "periodo sin precisar";
  };

  const textoFiltro = (filtros) => {
    if (!filtros) return "";
    const items = [];
    if (filtros.territorio || filtros.territorio_dane) items.push(`📍 ${filtros.territorio || filtros.territorio_dane}`);
    if (filtros.periodo) items.push(`📅 ${textoPeriodo(filtros.periodo)}`);
    if (filtros.estado_contrato) items.push(`📄 ${ESTADO_FRASE[filtros.estado_contrato] || filtros.estado_contrato}`);
    if (filtros.categoria_reporte) items.push(`👁️ Observaciones de ${(categorias[filtros.categoria_reporte] || filtros.categoria_reporte).toLowerCase()}`);
    if (filtros.con_reportes) items.push("🔗 Con reportes ciudadanos");
    if (filtros.con_relacion) items.push("🔗 Con posible conexión registrada");
    if (filtros.texto) items.push(`🔎 «${filtros.texto}»`);
    return items.length
      ? `<ul class="filtros filtros-entendidos">${items.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul>`
      : "";
  };

  const IA_TEXTO = {
    usada: "Interpretación asistida por IA",
    no_configurada: "Interpretación por reglas",
    fallo: "Interpretación por reglas (la IA no respondió; se usó el respaldo)",
  };

  const htmlResultadosBusqueda = () => {
    const b = estado.busqueda;
    if (!b) {
      return `<p class="muted">Escribe una pregunta en lenguaje corriente. No hace falta conocer el nombre del campo en SECOP.</p>`;
    }
    const contratos = b.contratos || [];
    const reportes = b.reportes || [];
    const fuentes = (b.fuentes || [])
      .map((f) => {
        if (f.url_fuente) {
          return `<li><a class="enlace" href="${escapeHtml(f.url_fuente)}" target="_blank" rel="noopener">${escapeHtml(f.id)}</a> · ${escapeHtml(f.fuente || "")}</li>`;
        }
        return `<li>${escapeHtml(f.tipo)} ${escapeHtml(f.id)} · ${escapeHtml(f.fuente || "")}</li>`;
      })
      .join("");
    const interpretacion = b.interpretacion || {};
    const iaTexto = IA_TEXTO[interpretacion.ia] || "Interpretación por reglas";
    const suficiente = interpretacion.suficiente !== false;
    return `
      ${estado.avisoZona ? `<p class="aviso">${escapeHtml(estado.avisoZona)}</p>` : ""}
      <h2>LADERA entendió</h2>
      <p class="muted">Interpretación automática · ${escapeHtml(iaTexto)}</p>
      ${
        suficiente
          ? textoFiltro(b.filtros)
          : `<p class="aviso">${escapeHtml(interpretacion.explicacion || "No pude identificar filtros suficientes. Puedes precisar municipio, año, estado o tema.")}</p>`
      }
      <h2>Contratos (${contratos.length})</h2>
      ${contratos.length ? `<ul class="lista">${contratos.map(tarjetaContrato).join("")}</ul>` : `<p class="muted">No se encontraron contratos identificados en el conjunto analizado que coincidan con esta pregunta.</p>`}
      <h2>Reportes (${reportes.length})</h2>
      ${reportes.length ? `<ul class="lista">${reportes.map(tarjetaReporte).join("")}</ul>` : `<p class="muted">No hay reportes que coincidan.</p>`}
      <h2>Fuentes</h2>
      ${fuentes ? `<ul class="fuentes">${fuentes}</ul>` : `<p class="muted">Sin fuentes en este recorte.</p>`}
      <p class="aviso">${escapeHtml(b.nota || "")}</p>
      ${
        (b.filtros && b.filtros.territorio_dane)
          ? `<p><button type="button" class="tarjeta" data-seguir="${escapeHtml(b.filtros.territorio_dane)}">Seguir el hilo en esta zona</button></p>`
          : estado.zonaDane
            ? `<p><button type="button" class="tarjeta" data-seguir="${escapeHtml(estado.zonaDane)}">Volver a la zona abierta</button></p>`
            : ""
      }
    `;
  };

  const vistaBuscar = () => `
      ${htmlHilo()}
      <p class="kicker">Buscar con lenguaje natural</p>
      <h1>Escribe lo que quieres saber, con tus propias palabras</h1>
      <p class="muted">Por ejemplo: «contratos activos de vías en Medellín que tengan reportes ciudadanos». No hace falta conocer los nombres técnicos de SECOP — LADERA lo convierte en filtros y te muestra exactamente qué entendió antes de buscar.</p>
      <form class="buscar" id="form-buscar">
        <input type="search" id="q" value="${escapeHtml(estado.q || "")}" placeholder="¿Qué quieres investigar?">
        <button type="submit">Buscar</button>
      </form>
      <p class="muted">Ejemplos:</p>
      <ul class="lista">
        <li><button type="button" class="tarjeta" data-pregunta="Muéstrame contratos que terminaron el año pasado y tienen reportes de obras inconclusas">Contratos que terminaron el año pasado con reportes de obras inconclusas</button></li>
        <li><button type="button" class="tarjeta" data-pregunta="¿Qué contratos hay relacionados con esta zona?">Contratos relacionados con esta zona</button></li>
        <li><button type="button" class="tarjeta" data-pregunta="Obras de mitigación de riesgo que siguen teniendo reportes ciudadanos">Mitigación de riesgo con reportes</button></li>
      </ul>
      <div id="resultados-busqueda">${htmlResultadosBusqueda()}</div>
    `;

  const aplicarHiloDesdeBusqueda = async (b) => {
    const f = (b && b.filtros) || {};
    estado.avisoZona = null;
    if (f.territorio_dane && f.territorio_dane !== estado.zonaDane) {
      const anterior = estado.zonaDane ? municipio(estado.zonaDane) : null;
      const nueva = municipio(f.territorio_dane);
      if (anterior && nueva) {
        estado.avisoZona = `Tu pregunta te movió a ${nueva.nombre}. Antes estabas en ${anterior.nombre}.`;
      }
      estado.zonaDane = f.territorio_dane;
    }
    let recortar = false;
    if (f.periodo && f.periodo.desde && f.periodo.hasta) {
      const y1 = String(f.periodo.desde).slice(0, 4);
      const y2 = String(f.periodo.hasta).slice(0, 4);
      if (y1 === y2) {
        estado.filtro.anio = y1;
        recortar = true;
      }
    }
    if (f.estado_contrato) {
      estado.filtro.estado = f.estado_contrato;
      recortar = true;
    }
    if (recortar) await cargarRecorte();
    await cargarHilo();
  };

  const lanzarBusqueda = async (pregunta) => {
    estado.q = pregunta;
    estado.vista = "buscar";
    marcarNav();
    const res = await fetch("/api/buscar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pregunta,
        dane: estado.zonaDane,
        usar_ia: true,
        sesion: estado.sesion,
      }),
    });
    const cuerpo = await res.json();
    if (!res.ok) {
      estado.busqueda = { interpretacion: { explicacion: cuerpo.error, metodo: "ERROR", ia: "apagada" }, filtros: {}, contratos: [], reportes: [], fuentes: [], nota: "" };
    } else {
      estado.busqueda = cuerpo;
      await aplicarHiloDesdeBusqueda(cuerpo);
      await cargarPiloto();
    }
    renderPanel();
  };

  const renderPanel = () => {
    if (estado.vista === "explorar") $panel.innerHTML = vistaExplorar();
    else if (estado.vista === "reportar") $panel.innerHTML = vistaReportar();
    else if (estado.vista === "buscar") $panel.innerHTML = vistaBuscar();
    else if (estado.seleccionado?.tipo === "municipio") $panel.innerHTML = vistaMunicipio(estado.seleccionado.id);
    else if (estado.seleccionado?.tipo === "contrato") $panel.innerHTML = vistaContrato(estado.seleccionado.id);
    else if (estado.seleccionado?.tipo === "reporte") $panel.innerHTML = vistaReporte(estado.seleccionado.id);
    else
      $panel.innerHTML = `${htmlHilo()}<p class="kicker">El mismo territorio</p><h1>Elige una zona</h1><p class="muted">El periodo y las capas recortan este mapa. Ver contratación y reportes en el mismo año no demuestra causa. Al elegir una zona sigues el hilo: contratos, valores, observaciones y relaciones.</p>
      <div class="zona-elegir">
        <label>Municipio (alternativa al mapa)
          <select id="select-municipio-zona" class="selector-municipio">${opcionesMunicipios("")}</select>
        </label>
      </div>`;

    const selectZona = document.getElementById("select-municipio-zona");
    if (selectZona) {
      selectZona.addEventListener("change", () => {
        if (selectZona.value) abrir({ tipo: "municipio", id: selectZona.value });
      });
    }

    const selectReportarMun = document.getElementById("select-municipio-reportar");
    if (selectReportarMun) {
      selectReportarMun.addEventListener("change", () => {
        if (selectReportarMun.value) {
          estado.zonaDane = selectReportarMun.value;
          centrarZona(selectReportarMun.value);
        }
      });
    }

    const form = document.getElementById("form-reporte");
    if (form) {
      ["input", "change"].forEach((evt) =>
        form.addEventListener(evt, (ev) => {
          const campo = ev.target;
          if (!campo.name || campo.name === "foto" || campo.name === "lat" || campo.name === "lng") return;
          estado.borrador[campo.name] = campo.value;
        })
      );
      form.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        if (!estado.puntoReporte || !estado.puntoReporte.dane) {
          pintarCamposPunto("Marca un punto dentro de un municipio de Antioquia.");
          return;
        }
        const boton = form.querySelector('button[type="submit"]');
        const original = ocuparBoton(boton, "Enviando…");
        try {
          const fd = new FormData(form);
          fd.set("lat", String(estado.puntoReporte.lat));
          fd.set("lng", String(estado.puntoReporte.lng));
          const res = await fetch("/api/reportes", { method: "POST", body: fd });
          const creado = await res.json();
          if (!res.ok) {
            $panel.insertAdjacentHTML("beforeend", `<p class="aviso">${escapeHtml(creado.error)}</p>`);
            return;
          }
          quitarMarcadorBorrador();
          vaciarBorrador();
          estado.datos = await (await fetch("/api/datos")).json();
          await cargarRecorte();
          await cargarHilo();
          abrir({ tipo: "reporte", id: creado.id });
        } finally {
          liberarBoton(boton, original);
        }
      });
    }

    const directa = document.getElementById("form-directa");
    if (directa) {
      directa.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const boton = directa.querySelector('button[type="submit"]');
        const original = ocuparBoton(boton, "Guardando…");
        try {
          const fd = new FormData(directa);
          const res = await fetch("/api/relaciones", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              reporte_id: estado.seleccionado && estado.seleccionado.tipo === "reporte" ? estado.seleccionado.id : "",
              contrato_id: fd.get("contrato_id"),
            }),
          });
          const cuerpo = await res.json();
          if (!res.ok) {
            $panel.insertAdjacentHTML("beforeend", `<p class="aviso">${escapeHtml(cuerpo.error)}</p>`);
            return;
          }
          estado.datos = await (await fetch("/api/datos")).json();
          await cargarRecorte();
          renderPanel();
        } finally {
          liberarBoton(boton, original);
        }
      });
    }

    const recargarTrasConfianza = async (res, creado) => {
      if (!res.ok) {
        $panel.insertAdjacentHTML("beforeend", `<p class="aviso">${escapeHtml(creado.error)}</p>`);
        return false;
      }
      estado.datos = await (await fetch("/api/datos")).json();
      await cargarRecorte();
      renderPanel();
      return true;
    };

    const formSenalar = document.getElementById("form-senalar");
    if (formSenalar) {
      formSenalar.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const boton = formSenalar.querySelector('button[type="submit"]');
        const original = ocuparBoton(boton, "Enviando…");
        try {
          const id = estado.seleccionado && estado.seleccionado.tipo === "reporte" ? estado.seleccionado.id : "";
          const fd = new FormData(formSenalar);
          const res = await fetch(`/api/reportes/${encodeURIComponent(id)}/senalar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ motivo: fd.get("motivo") }),
          });
          await recargarTrasConfianza(res, await res.json());
        } finally {
          liberarBoton(boton, original);
        }
      });
    }

    const formRevisarRep = document.getElementById("form-revisar-reporte");
    if (formRevisarRep) {
      formRevisarRep.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const boton = formRevisarRep.querySelector('button[type="submit"]');
        const original = ocuparBoton(boton, "Guardando…");
        try {
          const id = estado.seleccionado && estado.seleccionado.tipo === "reporte" ? estado.seleccionado.id : "";
          const fd = new FormData(formRevisarRep);
          const res = await fetch(`/api/reportes/${encodeURIComponent(id)}/revisar`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Moderacion-Token": estado.moderacionToken || "" },
            body: JSON.stringify({
              estado: fd.get("estado"),
              motivo: fd.get("motivo"),
              actor: fd.get("actor") || undefined,
            }),
          });
          await recargarTrasConfianza(res, await res.json());
        } finally {
          liberarBoton(boton, original);
        }
      });
    }

    const formRetirar = document.getElementById("form-retirar");
    if (formRetirar) {
      formRetirar.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const seguro = await confirmarAccion({
          titulo: "Retirar observación",
          texto:
            "Esto saca el reporte del mapa y de la búsqueda. El registro y su auditoría no se borran: sigue existiendo, solo deja de ser público. Puede volver a EN_REVISIÓN más adelante.",
          textoConfirmar: "Retirar observación",
          textoCancelar: "Cancelar",
        });
        if (!seguro) return;
        const boton = formRetirar.querySelector('button[type="submit"]');
        const original = ocuparBoton(boton, "Retirando…");
        try {
          const id = estado.seleccionado && estado.seleccionado.tipo === "reporte" ? estado.seleccionado.id : "";
          const fd = new FormData(formRetirar);
          const res = await fetch(`/api/reportes/${encodeURIComponent(id)}/retirar`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-Moderacion-Token": estado.moderacionToken || "" },
            body: JSON.stringify({ motivo: fd.get("motivo") }),
          });
          await recargarTrasConfianza(res, await res.json());
        } finally {
          liberarBoton(boton, original);
        }
      });
    }

    const formBuscar = document.getElementById("form-buscar");
    if (formBuscar) {
      const q = document.getElementById("q");
      if (q) {
        q.addEventListener("input", () => {
          estado.q = q.value;
        });
      }
      formBuscar.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const pregunta = (document.getElementById("q") || {}).value || "";
        if (!pregunta.trim()) return;
        const boton = formBuscar.querySelector('button[type="submit"]');
        const original = ocuparBoton(boton, "Buscando…");
        try {
          await lanzarBusqueda(pregunta.trim());
        } finally {
          liberarBoton(boton, original);
        }
      });
    }
  };

  const llenarAnios = () => {
    const sel = document.querySelector("#mapa-capas select[name=anio]");
    if (!sel || !estado.recorte) return;
    const actual = estado.filtro.anio;
    const opciones = ['<option value="">Todos</option>'].concat(
      (estado.recorte.anios || []).map((y) => `<option value="${y}"${String(y) === actual ? " selected" : ""}>${y}</option>`)
    );
    sel.innerHTML = opciones.join("");
  };

  const cargarRecorte = async () => {
    const q = new URLSearchParams();
    if (estado.filtro.anio) q.set("anio", estado.filtro.anio);
    if (estado.filtro.estado) q.set("estado", estado.filtro.estado);
    const res = await fetch(`/api/mapa?${q.toString()}`);
    estado.recorte = await res.json();
    llenarAnios();
    await cargarHilo();
    pintarCapa();
    marcarPuntos();
    if (estado.vista === "mapa" || (estado.seleccionado && estado.seleccionado.tipo === "municipio")) {
      renderPanel();
    }
  };

  const iniciarMapa = (geojson) => {
    estado.mapa = L.map("mapa", {
      zoomControl: false,
      attributionControl: false,
    });
    L.control.zoom({ position: "topright" }).addTo(estado.mapa);
    estado.capa = L.geoJSON(geojson, {
      style: (f) => estilo(f, false),
      onEachFeature: (feature, layer) => {
        const mun = municipio(daneDe(feature));
        layer.bindTooltip(mun ? mun.nombre : feature.properties.MPIO_CNMBR);
        layer.on("click", (ev) => {
          if (estado.vista === "reportar") {
            L.DomEvent.stopPropagation(ev);
            ponerPuntoReporte(ev.latlng, daneDe(feature));
            return;
          }
          abrir({ tipo: "municipio", id: daneDe(feature) });
        });
      },
    }).addTo(estado.mapa);
    estado.mapa.fitBounds(estado.capa.getBounds(), { padding: [16, 16] });
    marcarPuntos();
  };

  document.querySelectorAll(".nav button").forEach((b) => {
    b.addEventListener("click", () => irVista(b.dataset.vista));
  });

  const campoToken = document.getElementById("token-moderacion");
  if (campoToken) {
    campoToken.addEventListener("input", () => {
      estado.moderacionToken = campoToken.value;
    });
  }

  const botonPiloto = document.getElementById("ir-piloto");
  if (botonPiloto) {
    botonPiloto.addEventListener("click", () => irVista("piloto"));
  }

  const PIN_MODO_MODERADOR = "123";
  const botonModoModerador = document.getElementById("activar-modo-moderador");
  if (botonModoModerador) {
    botonModoModerador.addEventListener("click", () => {
      const pin = document.getElementById("pin-moderador");
      const aviso = document.getElementById("estado-modo-moderador");
      if (pin && pin.value === PIN_MODO_MODERADOR) {
        estado.modoModerador = true;
        if (pin) pin.value = "";
        if (aviso) aviso.hidden = false;
        renderPanel();
      }
    });
  }

  $panel.addEventListener("click", async (ev) => {
    const ir = ev.target.closest("[data-ir]");
    if (ir && $panel.contains(ir)) {
      irVista(ir.dataset.ir);
      return;
    }
    const seguir = ev.target.closest("[data-seguir]");
    if (seguir && $panel.contains(seguir)) {
      estado.zonaDane = seguir.dataset.seguir;
      abrir({ tipo: "municipio", id: estado.zonaDane });
      return;
    }
    const demo = ev.target.closest("[data-recorrido]");
    if (demo && $panel.contains(demo)) {
      estado.zonaDane = demo.dataset.recorrido;
      if (demo.dataset.anio) estado.filtro.anio = demo.dataset.anio;
      if (demo.dataset.pregunta) estado.q = demo.dataset.pregunta;
      await cargarRecorte();
      abrir({ tipo: "municipio", id: estado.zonaDane });
      return;
    }
    const ejemplo = ev.target.closest("[data-pregunta]");
    if (ejemplo && $panel.contains(ejemplo)) {
      const pregunta = ejemplo.dataset.pregunta;
      estado.q = pregunta;
      const cajaQ = document.getElementById("q");
      if (cajaQ) cajaQ.value = pregunta;
      await lanzarBusqueda(pregunta);
      return;
    }
    const revisar = ev.target.closest("[data-revisar]");
    if (revisar && $panel.contains(revisar)) {
      const [id, estadoRel] = revisar.dataset.revisar.split(":");
      const esConfirmar = estadoRel === "CONFIRMADA";
      const motivo = await pedirMotivo({
        titulo: esConfirmar ? "Confirmar conexión" : "Descartar conexión",
        texto: esConfirmar
          ? "Confirmar una conexión es un acto humano: no prueba que el contrato sea responsable ni que la obra se haya ejecutado. Explica por qué la confirmas."
          : "Explica por qué esta conexión no aplica.",
        textoOk: esConfirmar ? "Confirmar" : "Descartar",
      });
      if (motivo == null) return;
      const original = ocuparBoton(revisar, "Guardando…");
      const res = await fetch(`/api/relaciones/${encodeURIComponent(id)}/revisar`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Moderacion-Token": estado.moderacionToken || "" },
        body: JSON.stringify({ estado: estadoRel, motivo }),
      });
      const cuerpo = await res.json();
      if (!res.ok) {
        liberarBoton(revisar, original);
        $panel.insertAdjacentHTML("beforeend", `<p class="aviso">${escapeHtml(cuerpo.error)}</p>`);
        return;
      }
      estado.datos = await (await fetch("/api/datos")).json();
      await cargarRecorte();
      await cargarHilo();
      renderPanel();
      return;
    }
    const boton = ev.target.closest("[data-abrir]");
    if (!boton || !$panel.contains(boton)) return;
    const [tipo, id] = boton.dataset.abrir.split(":");
    abrir({ tipo, id });
  });

  const formCapas = document.getElementById("mapa-capas");
  if (formCapas) {
    formCapas.addEventListener("change", async (ev) => {
      const campo = ev.target;
      if (campo.type === "checkbox") {
        estado.capas[campo.name] = campo.checked;
        pintarCapa();
        marcarPuntos();
        return;
      }
      if (campo.name === "anio" || campo.name === "estado") {
        estado.filtro[campo.name] = campo.value;
        await cargarRecorte();
      }
    });
    formCapas.addEventListener("click", (ev) => ev.stopPropagation());
  }

  Promise.all([
    fetch("/api/datos").then((r) => r.json()),
    fetch("/assets/municipios_antioquia.geojson").then((r) => r.json()),
    fetch("/api/mapa").then((r) => r.json()),
    fetch("/api/piloto").then((r) => r.json()),
    fetch("/api/escala").then((r) => r.json()),
  ])
    .then(([datos, geojson, recorte, piloto, escala]) => {
      estado.datos = datos;
      estado.recorte = recorte;
      estado.piloto = piloto;
      estado.escala = escala;
      iniciarMapa(geojson);
      llenarAnios();
      pintarLeyenda();
      pintarPieFuente();
      renderPanel();
    })
    .catch((err) => {
      $panel.innerHTML = `<p>No se pudo cargar LADERA. ${escapeHtml(err.message)}</p>`;
    });
})();
