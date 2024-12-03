// サンプルデータ（実際の使用時は別ファイルから読み込むか、APIから取得します）
const sampleData = ["NaCl","HEPES","MOPS","Phosphoric acid","Acetic acid"]

// 入力フィールドとサジェスト要素の取得
const inputFields = ['a1', 'a2', 'b1', 'b2'].map(id => ({
    input: document.getElementById(`buffer-${id}`),
    suggestions: document.getElementById(`suggestions-${id}`),
    number: document.getElementById(`number-${id}`),
    addTagButton: document.getElementById(`add-tag-${id}`),
    tagContainer: document.getElementById(`tag-container-${id}`)
}));

// 各フィールドのタグを個別に管理
const tags = {
    a1: [], a2: [], b1: [], b2: []
};

// オートコンプリート機能の初期化
inputFields.forEach(field => {
    const { input, suggestions, number, addTagButton, tagContainer } = field;
    
    input.addEventListener('input', function() {
        const inputValue = this.value.toLowerCase();
        const fieldId = this.id.split('-')[1]; // 'buffer-a1' から 'a1' を取得
        const filteredSuggestions = sampleData.filter(item => 
            item.toLowerCase().includes(inputValue)
        );
        
        updateSuggestions(suggestions, filteredSuggestions, input);
    });

    input.addEventListener('focus', function() {
        if (this.value) {
            suggestions.classList.remove('hidden');
        }
    });

    input.addEventListener('blur', function() {
        // 少し遅延を入れて、サジェスト項目のクリックイベントが発火できるようにする
        setTimeout(() => {
            suggestions.classList.add('hidden');
        }, 200);
    });

    // 個別のタグ追加ボタンのイベントリスナー
    addTagButton.addEventListener('click', () => {
        const fieldId = input.id.split('-')[1];
        if (input.value && number.value) {
            addTag(fieldId, input.value, number.value);
            input.value = '';
            number.value = '';
        }
    });
});

// サジェスト一覧の更新
function updateSuggestions(suggestionsElement, items, inputElement) {
    suggestionsElement.innerHTML = '';
    
    if (items.length === 0) {
        suggestionsElement.classList.add('hidden');
        return;
    }

    items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        li.className = 'px-3 py-1 hover:bg-gray-100 cursor-pointer';
        li.addEventListener('click', () => {
            inputElement.value = item;
            suggestionsElement.classList.add('hidden');
        });
        suggestionsElement.appendChild(li);
    });

    suggestionsElement.classList.remove('hidden');
}

// タグの追加関数
function addTag(fieldId, text, number) {
    const tag = { text, number };
    tags[fieldId].push(tag);
    renderTags(fieldId);
}

// タグの描画
function renderTags(fieldId) {
    const tagContainer = document.getElementById(`tag-container-${fieldId}`);
    tagContainer.innerHTML = '';
    tags[fieldId].forEach((tag, index) => {
        const tagElement = document.createElement('div');
        tagElement.className = 'bg-gray-200 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 mr-2 mb-2';
        tagElement.innerHTML = `
            ${tag.text} (${tag.number})
            <button class="ml-2 text-gray-500 hover:text-gray-700" onclick="removeTag('${fieldId}', ${index})">×</button>
        `;
        tagContainer.appendChild(tagElement);
    });
}

// タグの削除
function removeTag(fieldId, index) {
    tags[fieldId].splice(index, 1);
    renderTags(fieldId);
}