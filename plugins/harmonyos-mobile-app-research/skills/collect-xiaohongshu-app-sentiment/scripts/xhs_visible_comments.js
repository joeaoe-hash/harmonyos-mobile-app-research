(async () => {
  const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
  const clean = (value) => (value || '').replace(/\s+/g, ' ').trim();
  const comments = new Map();
  const totalElement = [...document.querySelectorAll('.total')]
    .find((element) => /\d+/.test(clean(element.textContent)));
  const totalMatch = clean(totalElement ? totalElement.textContent : '').match(/\d+/);
  const expectedTotal = totalMatch ? Number(totalMatch[0]) : 0;
  const scroller = document.querySelector('.note-container') || document.querySelector('.note-scroller');

  const profileData = (item) => {
    const profile = [...item.querySelectorAll('a')]
      .find((anchor) => (anchor.getAttribute('href') || '').includes('/user/profile/'));
    const href = profile ? profile.getAttribute('href') || '' : '';
    const match = href.match(/\/user\/profile\/([a-zA-Z0-9]+)/);
    return { user_id: match ? match[1] : '', profile_url: match ? href : '' };
  };

  const addItem = (item, parentId, rootId, level) => {
    if (!item) return;
    const author = clean(item.querySelector('.author-wrapper .name, .user-name, .name')?.textContent);
    const text = clean(item.querySelector('.content, .note-text')?.textContent);
    const timeLocation = clean(item.querySelector('.info .date, .date, .time')?.textContent);
    const likesText = clean(item.querySelector('.interactions .like .count, .like .count')?.textContent);
    const imageUrls = [...item.querySelectorAll('.comment-picture img')]
      .map((image) => image.getAttribute('src') || '')
      .filter(Boolean);
    if (!text && imageUrls.length === 0) return;
    const commentId = (item.id || '').replace(/^comment-/, '');
    const key = commentId || `${level}|${author}|${text}|${timeLocation}|${imageUrls.join('|')}`;
    const profile = profileData(item);
    comments.set(key, {
      comment_id: commentId,
      parent_id: parentId || '',
      root_comment_id: rootId || commentId,
      author,
      user_id: profile.user_id,
      profile_url: profile.profile_url,
      text,
      image_urls: imageUrls,
      likes: /^\d+$/.test(likesText) ? Number(likesText) : 0,
      time_location: timeLocation,
      is_reply: level > 0,
      level,
    });
  };

  const collect = () => {
    for (const parent of document.querySelectorAll('.parent-comment')) {
      const parentItem = [...parent.children].find((child) =>
        child.classList && child.classList.contains('comment-item'));
      const rootId = (parentItem?.id || '').replace(/^comment-/, '');
      addItem(parentItem, '', rootId, 0);
      for (const reply of parent.querySelectorAll('.comment-item-sub')) {
        addItem(reply, rootId, rootId, 1);
      }
    }
  };

  const expandVisibleReplies = async () => {
    let changed = false;
    for (let round = 0; round < 40; round += 1) {
      const expanders = [...document.querySelectorAll('.show-more')]
        .filter((element) => /展开|更多|全部|查看/.test(clean(element.textContent)) && element.offsetParent !== null);
      if (expanders.length === 0) break;
      for (const expander of expanders) {
        expander.click();
        changed = true;
        await wait(350);
      }
      await wait(650);
      collect();
    }
    return changed;
  };

  if (scroller) scroller.scrollTo(0, 0);
  let plateauRounds = 0;
  let rounds = 0;
  const maxRounds = expectedTotal > 0 ? Math.min(500, Math.max(40, Math.ceil(expectedTotal / 4) + 30)) : 120;
  for (rounds = 0; rounds < maxRounds; rounds += 1) {
    const beforeCount = comments.size;
    const beforeHeight = scroller ? scroller.scrollHeight : document.body.scrollHeight;
    collect();
    const expanded = await expandVisibleReplies();
    collect();
    if (expectedTotal > 0 && comments.size >= expectedTotal) break;
    if (scroller) scroller.scrollTo(0, scroller.scrollHeight);
    else window.scrollTo(0, document.body.scrollHeight);
    await wait(1300);
    collect();
    const afterHeight = scroller ? scroller.scrollHeight : document.body.scrollHeight;
    const grew = comments.size > beforeCount || afterHeight > beforeHeight || expanded;
    plateauRounds = grew ? 0 : plateauRounds + 1;
    if (plateauRounds >= 6) break;
  }
  await expandVisibleReplies();
  collect();
  return {
    expected_total: expectedTotal,
    collected_total: comments.size,
    complete: expectedTotal > 0 ? comments.size >= expectedTotal : plateauRounds >= 6,
    plateau_rounds: plateauRounds,
    rounds,
    page_url: location.href,
    comments: [...comments.values()],
  };
})()
