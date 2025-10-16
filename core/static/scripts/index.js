// document.querySelectorAll('.category-card').forEach(btn => {
//       btn.addEventListener('click', function(e) {
//       const ripple = document.createElement('span');
//       ripple.classList.add('ripple');
                
                
//       const rect = btn.getBoundingClientRect();
//       const size = Math.max(rect.width, rect.height);
//       ripple.style.width = ripple.style.height = `${size}px`;
//       ripple.style.left = `${e.clientX - rect.left - size/2}px`;
//       ripple.style.top = `${e.clientY - rect.top - size/2}px`;
                
//       btn.appendChild(ripple);
                
//       // Удаляем элемент после анимации
//       setTimeout(() => ripple.remove(), 600);
//     });
// });

// document.querySelectorAll('folder-card').forEach(btn=>{
//   const ripple = document.createElement('span');
//   ripple.classList.add('ripple-folders');

//   const rect = btn.getBoundingClientRect();
//   const size = Math.max(rect.width, rect.height);
//   ripple.style.width = ripple.style.height = `${size}px`;
//   ripple.style.left = `${e.clientX - rect.left - size/2}px`;
//   ripple.style.top = `${e.clientY - rect.top - size/2}px`;


//   btn.appendChild(ripple);
//   setTimeout(() => ripple.remove(), 600);

// })


async function get_provider_info(params) {
  try{
    const response = await fetch("/test")
    const data = await response.json()
    const api_result_str = data["api result"]
    
    const jsonString = api_result_str
    .replace(/'/g, '"') // Replace single quotes with double quotes
    .replace(/\\\\/g, '\\') // Replace double backslashes with a single backslash
    .replace(/\\x1b/g, ''); // (optional) Remove specific unwanted escape sequences
    const parsedData = JSON.parse(jsonString);
    const raw_storage_data = parsedData.output;
    console.log(raw_storage_data)

        const storageProviderMatch = raw_storage_data.match(/Storage provider\s+([0-9A-Fa-f:]+)/);
        if (storageProviderMatch) {
            const raw_storage_provider = storageProviderMatch[0].trim(); 
            // console.log(`Storage Provider: ${raw_storage_provider}`);
            const storage_provider_parts = raw_storage_data.split(' ')
            console.log(storage_provider_parts[3].trim())

            storage_provider_el = document.getElementById('storage-provider')
            storage_provider_el.textContent = storage_provider_parts[3].trim()

        } else {
            console.log("Storage provider information not found.");
        }

    const totalSizeMatch = raw_storage_data.match(/Total size: (\d+B) \/ (\d+GB)/);
    // console.log(totalSizeMatch)

  if (totalSizeMatch) {
    const totalSizeValue = totalSizeMatch[1]; // e.g., "0B"
    const totalSizeLimit = totalSizeMatch[2]; // e.g., "128GB"
    const storageProvider = totalSizeLimit[0];
    console.log(`Total Size Value: ${totalSizeValue}`); 
    console.log(`Total Size Limit: ${totalSizeLimit}`);

    storage_status_el = document.getElementById('storage-status')
    storage_status_el.textContent = totalSizeValue + " are used out of " + totalSizeLimit


  } else {
    console.log("Total size information not found.");
  }

  }catch (error){
    console.error('Error fetching data', error);

    const storageStatusEl = document.getElementById('storage-status');
    if(storageStatusEl){
      storageStatusEl.textContent = 'Error loading storage data';
    }
  }
}

document.addEventListener('DOMContentLoaded', function(){
  get_provider_info();

  setInterval(get_provider_info, 60000)
})