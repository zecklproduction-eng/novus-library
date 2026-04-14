import re

paths = [
    r'd:\nist project\computer\library\novus-library\templates\community.html',
    r'd:\nist project\computer\library\novus-library\templates\group.html'
]

new_func = r"""
    // Gift Picker Logic (Enhanced)
    window.openCommentGiftPicker = function (postId, btn) {
        let existing = document.querySelector('.picker-popup');
        if (existing) { existing.remove(); return; }

        const rect = btn.getBoundingClientRect();
        const picker = document.createElement('div');
        picker.className = 'picker-popup';
        picker.style.cssText = `position: fixed; bottom: ${window.innerHeight - rect.top + 8}px; left: ${rect.left}px; background: var(--community-card-bg); border: 1px solid var(--community-card-border); padding: 12px; border-radius: 12px; display: flex; flex-direction: column; gap: 12px; z-index: 10001; width: 320px; box-shadow: 0 8px 24px rgba(0,0,0,0.4); font-family: inherit;`;

        // Header with Buy Coins button
        picker.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 8px;">
                <span style="color: #fff; font-weight: bold; font-size: 14px;">Gift Shop</span>
                <button id="buyCoinsBtn" style="background: var(--community-cyan); color: #000; border: none; border-radius: 4px; padding: 4px 8px; font-size: 12px; font-weight: bold; cursor: pointer;">
                    Buy Coins (+500)
                </button>
            </div>
            <div id="giftGrid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;"></div>
        `;

        document.body.appendChild(picker);

        document.getElementById('buyCoinsBtn').onclick = async (e) => {
            e.stopPropagation();
            try {
                const res = await fetch('/api/buy_coins', { method: 'POST' });
                const data = await res.json();
                if(data.success) {
                    alert(`Success! You now have ${data.coins} coins.`);
                } else {
                    alert(data.message);
                }
            } catch(err) { console.error(err); }
        };

        const giftGrid = document.getElementById('giftGrid');
        const gifts = [
            { icon: '🌹', name: 'Rose', price: 10, charisma: 5 },
            { icon: '🍰', name: 'Cake', price: 20, charisma: 10 },
            { icon: '🍻', name: 'Beer', price: 30, charisma: 15 },
            { icon: '🎁', name: 'Mystery Box', price: 50, charisma: 25 },
            { icon: '💖', name: 'Heart', price: 80, charisma: 40 },
            { icon: '💎', name: 'Diamond', price: 100, charisma: 50 },
            { icon: '🏆', name: 'Trophy', price: 500, charisma: 250 },
            { icon: '👑', name: 'Crown', price: 1000, charisma: 500 }
        ];

        gifts.forEach(gift => {
            const div = document.createElement('div');
            div.style.cssText = `display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; padding: 8px 4px; border-radius: 8px; transition: background 0.2s; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05);`;
            div.innerHTML = `
                <span style="font-size: 28px; line-height: 1;">${gift.icon}</span>
                <span style="font-size: 10px; color: #aaa; margin-top: 4px; text-align: center; line-height: 1.2;">
                    <span style="color: gold;">🪙 ${gift.price}</span><br>
                    <span style="color: #ff4081;">✨ +${gift.charisma}</span>
                </span>
            `;
            div.onmouseover = () => div.style.background = 'rgba(255,255,255,0.1)';
            div.onmouseout = () => div.style.background = 'rgba(0,0,0,0.2)';

            div.onclick = async function (e) {
                e.stopPropagation();
                if (!confirm(`Send ${gift.name} for ${gift.price} coins?`)) return;
                
                try {
                    const res = await fetch(`/group/post/${postId}/send_gift`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            gift_name: gift.name,
                            price: gift.price,
                            charisma: gift.charisma,
                            url: gift.icon
                        })
                    });
                    const data = await res.json();
                    if(data.success) {
                        alert(`Gift sent! Your balance: ${data.coins} coins.`);
                        picker.remove();
                        const cSec = document.getElementById(`comments-section-${postId}`);
                        if(cSec) cSec.style.display = 'block';
                        if(window.loadComments) window.loadComments(postId);
                    } else {
                        alert('Error: ' + data.message);
                    }
                } catch(err) { console.error(err); alert('Failed to send gift'); }
            };
            giftGrid.appendChild(div);
        });

        setTimeout(() => {
            document.addEventListener('click', function close(e) {
                if (!picker.contains(e.target) && e.target !== btn) {
                    picker.remove();
                    document.removeEventListener('click', close);
                }
            });
        }, 100);
    };
"""

for path in paths:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to find window.openCommentGiftPicker = function ... until next window.openCommentEmojiPicker
    # It assumes openCommentEmojiPicker comes next
    pattern = re.compile(r'window\.openCommentGiftPicker\s*=\s*function.*?(?=window\.openCommentEmojiPicker)', re.DOTALL)
    
    if pattern.search(content):
        # Substitute
        new_content = pattern.sub(new_func + "\n    ", content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {path}")
    else:
        print(f"Failed to find pattern in {path}")
