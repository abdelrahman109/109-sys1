document.addEventListener('DOMContentLoaded', () => {
  const bindWeaponSelect = (collegeId, weaponId, endpointBase) => {
    const collegeSelect = document.getElementById(collegeId);
    const weaponSelect = document.getElementById(weaponId);
    if (!collegeSelect || !weaponSelect || !endpointBase) return;

    const loadWeapons = async (preserveCurrent = false) => {
      const collegeValue = collegeSelect.value;
      const selectedValue = weaponSelect.dataset.selected || (preserveCurrent ? weaponSelect.value : '');
      weaponSelect.innerHTML = '<option value="">اختر</option>';
      if (!collegeValue) return;
      try {
        const res = await fetch(endpointBase + collegeValue);
        const data = await res.json();
        (data.weapons || []).forEach(item => {
          const opt = document.createElement('option');
          opt.value = String(item.id);
          opt.textContent = item.name_ar;
          if (selectedValue && String(selectedValue) === String(item.id)) {
            opt.selected = true;
          }
          weaponSelect.appendChild(opt);
        });
      } catch (err) {
        console.error('Failed to load weapons', err);
      }
    };

    collegeSelect.addEventListener('change', async () => {
      weaponSelect.dataset.selected = '';
      await loadWeapons(false);
    });

    loadWeapons(true);
  };

  const registerForm = document.getElementById('registerForm');
  if (registerForm) bindWeaponSelect('collegeSelect', 'weaponSelect', registerForm.dataset.weaponsEndpoint);

  const profileForm = document.getElementById('profileForm');
  if (profileForm) bindWeaponSelect('profileCollegeSelect', 'profileWeaponSelect', profileForm.dataset.weaponsEndpoint);

  const martyrForm = document.getElementById('martyrForm');
  if (martyrForm) bindWeaponSelect('martyrCollegeSelect', 'martyrWeaponSelect', martyrForm.dataset.weaponsEndpoint);

  document.querySelectorAll('.donation-card[data-expires-at]').forEach(card => {
    const timer = card.querySelector('.timer');
    const expiresAt = new Date(card.dataset.expiresAt.replace(' ', 'T') + 'Z');
    const tick = () => {
      const diff = Math.max(0, Math.floor((expiresAt - new Date()) / 1000));
      const mins = String(Math.floor(diff / 60)).padStart(2, '0');
      const secs = String(diff % 60).padStart(2, '0');
      if (timer) timer.textContent = `${mins}:${secs}`;
      if (diff <= 0) clearInterval(interval);
    };
    tick();
    const interval = setInterval(tick, 1000);
  });
});
