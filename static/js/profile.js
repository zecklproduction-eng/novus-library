const avatarInput = document.getElementById("avatarInput");
  const previewImg = document.getElementById("avatarPreviewImg");
  if (avatarInput && previewImg) {
    avatarInput.addEventListener("change", () => {
      const file = avatarInput.files && avatarInput.files[0];
      if (!file) return;
      const url = URL.createObjectURL(file);
      previewImg.src = url;
    });
  }