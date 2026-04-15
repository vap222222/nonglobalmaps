const fs = require('fs');
const https = require('https');

// Helper to fetch JSON from API
async function fetchJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'Accept': 'application/json' } }, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        if (res.statusCode === 200) resolve(JSON.parse(data));
        else reject(new Error(`Status: ${res.statusCode}`));
      });
    }).on('error', reject);
  });
}

async function updateRecords(mode, filePath) {
  console.log(`Fetching latest WRs for ${mode}...`);
  const url = `https://api.cs2kz.org/records?mode=${mode}&max_rank=1&limit=20`;
  
  try {
    const response = await fetchJson(url);
    const records = response.values || [];
    
    // We only save the fields your app needs to save space
    const simplified = records.map(r => ({
      id: r.id,
      player_name: r.player?.name || 'Unknown',
      map_name: r.map?.name || 'Unknown',
      time: r.time,
      teleports: r.teleports,
      created_on: r.created_on,
      mode: r.mode
    }));

    fs.writeFileSync(filePath, JSON.stringify(simplified, null, 2));
    console.log(`Successfully updated ${filePath}`);
  } catch (e) {
    console.error(`Failed to update ${mode}:`, e.message);
  }
}

async function run() {
  await updateRecords('vanilla', 'data/vnl_wrs.json');
  await updateRecords('classic', 'data/ckz_wrs.json');
}

run();
