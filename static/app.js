document.addEventListener('click', async (e) => {
  if (e.target.matches('.approve')) {
    const clip = e.target.closest('.clip');
    const id = clip.dataset.clipid;
    await fetch(`/projects/1/clips/${id}/approve`, { method: 'POST' });
    clip.style.border = '2px solid green';
  }
  if (e.target.matches('.reject')) {
    const clip = e.target.closest('.clip');
    const id = clip.dataset.clipid;
    await fetch(`/projects/1/clips/${id}/reject`, { method: 'POST' });
    clip.style.opacity = 0.5;
  }
  if (e.target.matches('.render')) {
    const clip = e.target.closest('.clip');
    const id = clip.dataset.clipid;
    await fetch(`/projects/1/clips/${id}/render`, { method: 'POST' });
    e.target.textContent = 'Queued';
  }
  if (e.target.matches('#assemble')) {
    const btn = e.target;
    btn.textContent = 'Assembling...';
    const res = await fetch(`/projects/1/assemble`, { method: 'POST' });
    const j = await res.json();
    btn.textContent = 'Assemble Longform (12 min)';
    if (j.out) {
      const dl = document.getElementById('download');
      dl.href = j.out.replace('C:', '');
      dl.style.display = 'inline';
    }
  }
});
