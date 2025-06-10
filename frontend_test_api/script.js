const API_URL = "http://127.0.0.1:8000"; // поменяй на свой, если нужно

async function invest() {
  const user_id = Number(document.getElementById("userId").value);
  const amount = parseFloat(document.getElementById("investAmount").value);
  const pool_name = document.getElementById("pool").value;
  const use_balance = document.getElementById("useBalance").checked;

  const payload = {
    user_id,
    amount,
    pool_name,
    use_balance
  };

  const res = await fetch(`${API_URL}/invest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  const text = await res.text();
  document.getElementById("response").innerText = text;
}

async function toggleReinvest(enabled) {
  const user_id = Number(document.getElementById("userId").value);

  const res = await fetch(`${API_URL}/reinvest/settings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, enabled })
  });

  const text = await res.text();
  document.getElementById("response").innerText = text;
}

async function withdraw() {
  const user_id = Number(document.getElementById("userId").value);
  const amount = parseFloat(document.getElementById("withdrawAmount").value);
  const method = document.getElementById("method").value;
  const address = document.getElementById("address").value;

  const res = await fetch(`${API_URL}/withdraw`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, amount_usd: amount, method, address })
  });

  const text = await res.text();
  document.getElementById("response").innerText = text;
}
