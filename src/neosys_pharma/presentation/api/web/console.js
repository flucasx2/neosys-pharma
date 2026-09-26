const api = "/api/v1";
const state = { articles: [], vente: null };
const $ = (id) => document.getElementById(id);
const money = (value) => `${Number(value).toLocaleString("fr-FR")} FCFA`;
const safe = (value) => String(value).replace(/[&<>"]/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;",
}[char]));

function message(text = "", type = "") {
  $("message").textContent = text;
  $("message").className = type;
}

async function request(path, options = {}) {
  const response = await fetch(`${api}${path}`, {
    headers: { "Content-Type": "application/json" }, ...options,
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Une erreur est survenue.");
  return data;
}

function renderArticles() {
  const term = $("recherche").value.trim().toLowerCase();
  const articles = state.articles.filter((item) =>
    [item.designation, item.reference, item.code, item.libelle]
      .some((value) => value.toLowerCase().includes(term))
  );
  $("article-count").textContent = `${articles.length} article${articles.length > 1 ? "s" : ""}`;
  $("articles").innerHTML = articles.length ? articles.map((item) => `
    <article class="article">
      <div><h3>${safe(item.designation)}</h3><p>${safe(item.reference)} · ${safe(item.libelle)} · ${safe(item.code)}</p></div>
      <div class="article-price"><span>${money(item.prix_vente)}</span>
        <button data-add="${item.id}">Ajouter</button></div>
    </article>`).join("") : '<div class="empty">Aucun article trouvé.</div>';
}

function renderVente() {
  const vente = state.vente;
  $("vente-label").textContent = vente ? vente.numero_ticket : "Aucune vente ouverte";
  $("etat").textContent = vente ? vente.etat.replaceAll("_", " ") : "—";
  $("total").textContent = money(vente?.montant_total || 0);
  $("lignes").innerHTML = vente?.lignes.length ? vente.lignes.map((ligne) => `
    <div class="cart-line"><div><strong>${safe(ligne.designation)}</strong>
      <small>${ligne.quantite} × ${money(ligne.prix_unitaire)}</small></div>
      <div class="line-amount">${money(ligne.montant)}</div></div>`).join("")
    : '<div class="empty">Ajoutez un article depuis le catalogue.</div>';
  const ouverte = vente && vente.etat === "en_preparation";
  $("preparer").disabled = !ouverte || vente.lignes.length === 0;
  $("annuler").disabled = !vente || vente.etat === "annulee";
}

async function charger() {
  try {
    const [postes, articles] = await Promise.all([
      request("/ventes/postes"), request("/catalogue/articles"),
    ]);
    $("poste").innerHTML = postes.length
      ? postes.map((p) => `<option value="${p.id}">${p.code}</option>`).join("")
      : '<option value="">Aucun poste disponible</option>';
    state.articles = articles;
    renderArticles();
  } catch (error) { message(error.message, "error"); }
}

$("nouvelle-vente").addEventListener("click", async () => {
  const posteId = $("poste").value;
  if (!posteId) return message("Créez d’abord un poste de vente.", "error");
  try {
    state.vente = await request("/ventes", {
      method: "POST", body: JSON.stringify({
        poste_id: posteId, date_commerciale: new Date().toISOString().slice(0, 10),
      }),
    });
    message("Nouvelle vente créée.", "success");
    renderVente();
  } catch (error) { message(error.message, "error"); }
});

$("articles").addEventListener("click", async (event) => {
  const id = event.target.dataset.add;
  if (!id) return;
  if (!state.vente || state.vente.etat !== "en_preparation")
    return message("Ouvrez d’abord une nouvelle vente.", "error");
  try {
    await request(`/ventes/${state.vente.id}/lignes`, {
      method: "POST", body: JSON.stringify({ conditionnement_id: id, quantite: 1 }),
    });
    state.vente = await request(`/ventes/${state.vente.id}`);
    message("Article ajouté au panier.", "success");
    renderVente();
  } catch (error) { message(error.message, "error"); }
});

$("preparer").addEventListener("click", async () => {
  try {
    const ventePreparee = await request(`/ventes/${state.vente.id}/preparation`, { method: "POST" });
    state.vente = null;
    message(`Préparation validée. Ticket ${ventePreparee.numero_ticket}. Écran prêt pour la vente suivante.`, "success");
    renderVente();
  } catch (error) { message(error.message, "error"); }
});

$("annuler").addEventListener("click", async () => {
  if (!confirm("Annuler cette vente et libérer le stock réservé ?")) return;
  try {
    state.vente = await request(`/ventes/${state.vente.id}/annulation`, { method: "POST" });
    message("Vente annulée. Les réservations ont été libérées.", "success");
    renderVente();
  } catch (error) { message(error.message, "error"); }
});

$("recherche").addEventListener("input", renderArticles);
renderVente();
charger();
