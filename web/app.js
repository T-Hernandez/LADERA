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
    PUBLICADO: "Publicado",
    EN_REVISION: "En revisión",
    RELACIONADO: "Relacionado",
    VERIFICADO: "Verificado",
    DESCARTADO: "Descartado",
  };

  const escapeHtml = (valor) =>
    String(valor ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");

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

  const estilo = (feature, seleccionado) => {
    const mun = municipio(daneDe(feature));
    const tieneC = mun && mun.contratos > 0;
    const tieneR = mun && mun.reportes > 0;
    let fill = "#d9d2c4";
    let color = "#6a6256";
    let weight = 1;
    if (tieneC && tieneR) {
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
  };

  const limpiarMarcas = () => {
    estado.marcas.forEach((m) => m.remove());
    estado.marcas = [];
  };

  const marcarPuntos = () => {
    limpiarMarcas();
    if (!estado.mapa || !estado.datos) return;
    Object.values(estado.datos.reportes).forEach((rep) => {
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

  const abrir = (sel) => {
    estado.seleccionado = sel;
    if (sel) estado.vista = "mapa";
    pintarCapa();
    document.querySelectorAll(".nav button").forEach((b) => {
      b.classList.toggle("esta", b.dataset.vista === estado.vista);
    });
    renderPanel();
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

  const irVista = (vista) => {
    if (estado.vista === "reportar" && vista !== "reportar") quitarMarcadorBorrador();
    estado.vista = vista;
    if (vista !== "mapa") estado.seleccionado = null;
    pintarCapa();
    document.querySelectorAll(".nav button").forEach((b) => {
      b.classList.toggle("esta", b.dataset.vista === vista);
    });
    renderPanel();
  };

  const tarjetaContrato = (c) => `
    <li>
      <button type="button" class="tarjeta" data-abrir="contrato:${escapeHtml(c.id)}">
        <strong>${escapeHtml(c.id)}</strong> · ${escapeHtml(estadosContrato[c.estado] || c.estado)}
        <small>${escapeHtml(c.objeto)}</small>
        <small>${plata(c.valor)}</small>
      </button>
    </li>`;

  const etiquetaRelacion = (rel) => {
    if (rel.estado === "CONFIRMADA") return "Relación confirmada";
    if (rel.estado === "SUGERIDA") return "Posible relación";
    return "Relación descartada";
  };

  const accionesRelacion = (rel) => {
    if (rel.estado !== "SUGERIDA") return "";
    return `
      <p class="acciones-rel">
        <button type="button" class="secundario" data-revisar="${escapeHtml(rel.id)}:CONFIRMADA">Confirmar relación</button>
        <button type="button" class="secundario" data-revisar="${escapeHtml(rel.id)}:DESCARTADA">Descartar</button>
      </p>`;
  };

  const tarjetaReporte = (r) => `
    <li>
      <button type="button" class="tarjeta" data-abrir="reporte:${escapeHtml(r.id)}">
        <strong>${escapeHtml(categorias[r.categoria] || r.categoria)}</strong>
        <small>${escapeHtml(r.descripcion)}</small>
        <small>${escapeHtml(r.ubicacion.nombre)}${r.ubicacion.detalle ? " · " + escapeHtml(r.ubicacion.detalle) : ""}</small>
      </button>
    </li>`;

  const vistaExplorar = () => {
    const r = estado.datos.resumen;
    return `
      <p class="kicker">Fase 7 · contraste</p>
      <h1>Una superficie para contrastar</h1>
      <p class="muted">
        LADERA guarda lo que las personas observan y lo pone al lado de la
        contratación pública, que de otro modo es difícil de recorrer.
      </p>
      <div class="cifras">
        <div class="cifra"><b>${r.municipios}</b> municipios</div>
        <div class="cifra"><b>${r.contratos}</b> contratos (fixture)</div>
        <div class="cifra"><b>${r.reportes}</b> reportes</div>
        <div class="cifra"><b>${plata(r.plata_total)}</b> con cifra usable</div>
      </div>
      <h2>Cómo empezar</h2>
      <p class="muted">Haz clic en Medellín, Bello o Ituango. Son los tres casos del fixture.</p>
      <ul class="lista">
        <li><button type="button" class="tarjeta" data-abrir="municipio:05001">Medellín — contratos, dinero y un reporte con foto</button></li>
        <li><button type="button" class="tarjeta" data-abrir="municipio:05088">Bello — contratos, cero reportes</button></li>
        <li><button type="button" class="tarjeta" data-abrir="municipio:05361">Ituango — reporte sin relación contractual conocida</button></li>
      </ul>
      <p class="aviso">${escapeHtml(r.nota)}</p>
    `;
  };

  const vistaMunicipio = (dane) => {
    const mun = municipio(dane);
    if (!mun) return `<p>Municipio no encontrado.</p>`;
    const contratos = mun.contrato_ids.map(contrato).filter(Boolean);
    const reportes = mun.reporte_ids.map(reporte).filter(Boolean);
    return `
      <p class="kicker">Municipio · ${escapeHtml(mun.dane)}</p>
      <h1>${escapeHtml(mun.nombre)}</h1>
      <div class="cifras">
        <div class="cifra"><b>${mun.contratos}</b> contratos identificados</div>
        <div class="cifra"><b>${mun.reportes}</b> reportes</div>
        <div class="cifra"><b>${plata(mun.plata_total)}</b> suma usable</div>
        <div class="cifra"><b>${contratos.filter((c) => c.valor == null).length}</b> sin cifra usable</div>
      </div>
      <h2>Contratos</h2>
      ${contratos.length ? `<ul class="lista">${contratos.map(tarjetaContrato).join("")}</ul>` : `<p class="muted">Sin contratación identificada en el conjunto analizado.</p>`}
      <h2>Reportes</h2>
      ${reportes.length ? `<ul class="lista">${reportes.map(tarjetaReporte).join("")}</ul>` : `<p class="muted">Nadie ha publicado un reporte en este municipio todavía.</p>`}
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
         <p class="muted">El enlace sale del campo URLProceso. En este fixture es de demostración.</p>`
      : `<p class="muted">Este registro no trae URLProceso.</p>`;
    const lugares = (c.ubicaciones || [])
      .map((u) => `<li><strong>${escapeHtml(u.nombre)}</strong><small>Fragmento: “${escapeHtml(u.fragmento)}”</small></li>`)
      .join("");
    return `
      <p class="kicker">Contrato · ${escapeHtml(c.fuente)}</p>
      <h1>${escapeHtml(c.id)}</h1>
      <p><span class="estado">${escapeHtml(estadosContrato[c.estado] || c.estado)}</span></p>
      <p>${escapeHtml(c.objeto)}</p>
      <p class="muted">${escapeHtml(c.entidad)} · ${escapeHtml(c.municipio_nombre)}</p>
      <p>${plata(c.valor)}${c.valor_motivo ? ` <span class="muted">(${escapeHtml(c.valor_motivo)})</span>` : ""}</p>
      <p class="muted">${escapeHtml(c.fecha_inicio || "sin inicio")} → ${escapeHtml(c.fecha_fin || "sin fin")}</p>
      ${fuente}
      ${lugares ? `<h2>Lugares con fragmento</h2><ul class="lista">${lugares}</ul>` : ""}
      <p><button type="button" class="tarjeta" data-abrir="municipio:${escapeHtml(c.municipio_dane)}">Ver municipio ${escapeHtml(c.municipio_nombre)}</button></p>
      <h2>Reportes en contraste</h2>
      ${
        reportes.filter(({ rel }) => rel.estado !== "DESCARTADA").length
          ? reportes
              .filter(({ rel }) => rel.estado !== "DESCARTADA")
              .map(
                ({ rel, rep }) => `
            <p><span class="estado ${rel.estado.toLowerCase()}">${escapeHtml(etiquetaRelacion(rel))}</span></p>
            <p class="muted">${escapeHtml(rel.evidencia)}</p>
            <ul class="lista">${tarjetaReporte(rep)}</ul>
            ${accionesRelacion(rel)}`
              )
              .join("")
          : `<p class="muted">No hay una relación registrada con reportes.</p>`
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
      ${ev || `<p class="muted">Sin evidencia fotográfica.</p>`}
      <p><button type="button" class="tarjeta" data-abrir="municipio:${escapeHtml(r.ubicacion.dane)}">Ver ubicación municipal</button></p>
      <h2>Contraste con contratación</h2>
      ${
        contratos.filter(({ rel }) => rel.estado !== "DESCARTADA").length
          ? contratos
              .filter(({ rel }) => rel.estado !== "DESCARTADA")
              .map(
                ({ rel, con }) => `
            <p><span class="estado ${rel.estado.toLowerCase()}">${escapeHtml(etiquetaRelacion(rel))}</span></p>
            <p class="muted">${escapeHtml(rel.evidencia)}</p>
            <ul class="lista">${tarjetaContrato(con)}</ul>
            ${accionesRelacion(rel)}`
              )
              .join("")
          : `<p class="muted">No hay una relación contractual conocida para este reporte.</p>`
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
    `;
  };

  const vistaReportar = () => {
    const cats = Object.entries(categorias)
      .map(([k, v]) => `<option value="${k}">${escapeHtml(v)}</option>`)
      .join("");
    const punto = estado.puntoReporte || {};
    return `
      <p class="kicker">Nueva observación</p>
      <h1>Reportar</h1>
      <p class="muted">No necesitas conocer un contrato. Describe lo que observaste, márcalo en el mapa y, si puedes, adjunta una foto.</p>
      <form class="reporte" id="form-reporte">
        <p class="paso">1. Qué observaste</p>
        <label>Descripción
          <textarea name="descripcion" required maxlength="1200" placeholder="¿Qué viste en el territorio?"></textarea>
        </label>
        <label>Categoría
          <select name="categoria" required>${cats}</select>
        </label>
        <p class="paso">2. Dónde</p>
        <p class="punto-estado" id="punto-estado">${escapeHtml(textoPunto(estado.puntoReporte))}</p>
        <input type="hidden" name="lat" id="campo-lat" value="${punto.lat != null ? escapeHtml(punto.lat) : ""}">
        <input type="hidden" name="lng" id="campo-lng" value="${punto.lng != null ? escapeHtml(punto.lng) : ""}">
        <label>Lugar más específico (opcional)
          <input name="detalle" maxlength="160" placeholder="barrio, vereda, vía">
        </label>
        <p class="paso">3. Cuándo lo observaste</p>
        <label>Fecha de la observación
          <input name="fecha_observacion" type="date" required>
        </label>
        <p class="muted">La fecha en que envías el reporte la registra el sistema.</p>
        <p class="paso">4. Evidencia</p>
        <label>Fotografía (opcional)
          <input name="foto" type="file" accept="image/jpeg,image/png,image/webp,image/gif">
        </label>
        <label>Tu nombre o seudónimo (opcional)
          <input name="autor" maxlength="80">
        </label>
        <button type="submit">Enviar observación</button>
      </form>
      <p class="aviso">Queda en revisión en este equipo. No es un hecho verificado y no se vincula solo a un contrato.</p>
    `;
  };

  const htmlResultadosBusqueda = (q = "") => {
    const query = q.trim().toLowerCase();
    if (!query) {
      return `<p class="muted">Prueba “Popular”, “Niquía” o “movimiento en masa”.</p>`;
    }
    const contratos = Object.values(estado.datos.contratos).filter((c) =>
      [c.id, c.objeto, c.entidad, c.municipio_nombre, c.texto_original]
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
    const reportes = Object.values(estado.datos.reportes).filter((r) =>
      [r.descripcion, r.categoria, r.ubicacion.nombre, r.ubicacion.detalle, r.autor]
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
    return `
      <h2>Contratos</h2>
      ${contratos.length ? `<ul class="lista">${contratos.map(tarjetaContrato).join("")}</ul>` : `<p class="muted">No se encontraron contratos identificados en el conjunto analizado que coincidan con esta pregunta.</p>`}
      <h2>Reportes</h2>
      ${reportes.length ? `<ul class="lista">${reportes.map(tarjetaReporte).join("")}</ul>` : `<p class="muted">No hay reportes que coincidan.</p>`}
    `;
  };

  const vistaBuscar = (q = "") => `
      <p class="kicker">Conjunto analizado</p>
      <h1>Buscar</h1>
      <p class="muted">Palabras clave sobre el fixture. La interpretación con IA viene después, y se puede apagar.</p>
      <p class="buscar"><input type="search" id="q" value="${escapeHtml(q)}" placeholder="contención, Ituango, inconclusa…"></p>
      <div id="resultados-busqueda">${htmlResultadosBusqueda(q)}</div>
    `;

  const renderPanel = () => {
    if (estado.vista === "explorar") $panel.innerHTML = vistaExplorar();
    else if (estado.vista === "reportar") $panel.innerHTML = vistaReportar();
    else if (estado.vista === "buscar") $panel.innerHTML = vistaBuscar(estado.q || "");
    else if (estado.seleccionado?.tipo === "municipio") $panel.innerHTML = vistaMunicipio(estado.seleccionado.id);
    else if (estado.seleccionado?.tipo === "contrato") $panel.innerHTML = vistaContrato(estado.seleccionado.id);
    else if (estado.seleccionado?.tipo === "reporte") $panel.innerHTML = vistaReporte(estado.seleccionado.id);
    else $panel.innerHTML = `<p class="kicker">Mapa</p><h1>Elige un municipio</h1><p class="muted">Ciento veinticinco polígonos. El color dice si hay contratos, reportes, ambos o ninguno en el conjunto actual.</p>`;

    const form = document.getElementById("form-reporte");
    if (form) {
      form.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        if (!estado.puntoReporte || !estado.puntoReporte.dane) {
          pintarCamposPunto("Marca un punto dentro de un municipio de Antioquia.");
          return;
        }
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
        estado.datos = await (await fetch("/api/datos")).json();
        marcarPuntos();
        pintarCapa();
        abrir({ tipo: "reporte", id: creado.id });
      });
    }

    const directa = document.getElementById("form-directa");
    if (directa) {
      directa.addEventListener("submit", async (ev) => {
        ev.preventDefault();
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
        renderPanel();
      });
    }

    const q = document.getElementById("q");
    if (q) {
      q.focus();
      q.addEventListener("input", () => {
        estado.q = q.value;
        const caja = document.getElementById("resultados-busqueda");
        if (caja) caja.innerHTML = htmlResultadosBusqueda(estado.q);
      });
    }
  };

  const iniciarMapa = (geojson) => {
    estado.mapa = L.map("mapa", {
      zoomControl: true,
      attributionControl: false,
    });
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

  $panel.addEventListener("click", async (ev) => {
    const revisar = ev.target.closest("[data-revisar]");
    if (revisar && $panel.contains(revisar)) {
      const [id, estadoRel] = revisar.dataset.revisar.split(":");
      const res = await fetch(`/api/relaciones/${encodeURIComponent(id)}/revisar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estado: estadoRel }),
      });
      const cuerpo = await res.json();
      if (!res.ok) {
        $panel.insertAdjacentHTML("beforeend", `<p class="aviso">${escapeHtml(cuerpo.error)}</p>`);
        return;
      }
      estado.datos = await (await fetch("/api/datos")).json();
      renderPanel();
      return;
    }
    const boton = ev.target.closest("[data-abrir]");
    if (!boton || !$panel.contains(boton)) return;
    const [tipo, id] = boton.dataset.abrir.split(":");
    abrir({ tipo, id });
  });

  Promise.all([fetch("/api/datos").then((r) => r.json()), fetch("/assets/municipios_antioquia.geojson").then((r) => r.json())])
    .then(([datos, geojson]) => {
      estado.datos = datos;
      iniciarMapa(geojson);
      renderPanel();
    })
    .catch((err) => {
      $panel.innerHTML = `<p>No se pudo cargar LADERA. ${escapeHtml(err.message)}</p>`;
    });
})();
