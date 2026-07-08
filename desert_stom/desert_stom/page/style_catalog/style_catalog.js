frappe.pages['style-catalog'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Tailoring Style Catalog',
		single_column: true
	});

	inject_catalog_styles();

	$(wrapper).find('.layout-main-section').html(
		'<div class="sc-wrap">'
		+ '<div class="sc-header">'
		+   '<div class="sc-header-left">'
		+     '<div class="sc-header-title">Tailoring Style Catalog</div>'
		+     '<div class="sc-header-sub">Manage styles & garment options with images</div>'
		+   '</div>'
		+   '<button class="sc-add-btn" id="sc-add-btn">＋ Add New Style</button>'
		+ '</div>'
		+ '<div class="sc-filterbar">'
		+   '<div class="sc-tabs" id="sc-tabs"></div>'
		+ '</div>'
		+ '<div class="sc-content"><div class="sc-grid" id="sc-grid"></div></div>'
		+ '</div>'
	);

	var CATEGORIES = [
		'All',
		'Collar Style', 'Neck Style',
		'Collar Type', 'Neck Type',
		'Hip', 'Hip Type',
		'Special Button',
		'Thobe Model',
		'Garment Model',
		'Bottom Style',
		'Stitching Type',
		'Patty Model', 'Patty Type',
		'Front Pocket Type', 'Front Pocket Accessories',
		'Side Pocket Type', 'Side Pocket Accessories'
	];

	var currentCategory = 'All';
	var allItems = [];

	// Build category tabs
	var $tabs = $('#sc-tabs');
	CATEGORIES.forEach(function(cat) {
		var $t = $('<button class="sc-tab' + (cat === 'All' ? ' active' : '') + '">' + cat + '</button>');
		$t.on('click', function() {
			$tabs.find('.sc-tab').removeClass('active');
			$t.addClass('active');
			currentCategory = cat;
			renderGrid();
		});
		$tabs.append($t);
	});

	$('#sc-add-btn').on('click', function() {
		open_style_dialog(null, loadItems);
	});

	function loadItems() {
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'Style Option',
				fields: ['name', 'option_name', 'category', 'image'],
				limit_page_length: 500,
				order_by: 'category asc, option_name asc'
			},
			callback: function(r) {
				allItems = r.message || [];
				renderGrid();
			}
		});
	}

	function renderGrid() {
		var $grid = $('#sc-grid');
		var items = currentCategory === 'All'
			? allItems
			: allItems.filter(function(i) { return i.category === currentCategory; });

		if (!items.length) {
			$grid.html(
				'<div class="sc-empty">'
				+ '<div class="sc-empty-icon">🗂️</div>'
				+ '<div class="sc-empty-text">No styles yet</div>'
				+ '<div class="sc-empty-hint">Add styles with images to display them here</div>'
				+ '<button class="sc-empty-btn" id="sc-empty-add">＋ Add New Style</button>'
				+ '</div>'
			);
			$('#sc-empty-add').on('click', function() {
				open_style_dialog(null, loadItems);
			});
			return;
		}

		// Group by category when showing All
		var html = '';
		if (currentCategory === 'All') {
			var groups = {};
			items.forEach(function(item) {
				if (!groups[item.category]) groups[item.category] = [];
				groups[item.category].push(item);
			});
			Object.keys(groups).forEach(function(cat) {
				html += '<div class="sc-group">'
					+ '<div class="sc-group-header">'
					+   '<div class="sc-group-icon">✦</div>'
					+   '<div class="sc-group-title">' + cat + '</div>'
					+   '<span class="sc-group-count">' + groups[cat].length + '</span>'
					+   '<div class="sc-group-line"></div>'
					+ '</div>'
					+ '<div class="sc-cards">' + buildCards(groups[cat]) + '</div>'
					+ '</div>';
			});
		} else {
			html = '<div class="sc-cards">' + buildCards(items) + '</div>';
		}

		$grid.html(html);
		bindCardEvents();
	}

	function buildCards(items) {
		return items.map(function(item) {
			var imgHtml = item.image
				? '<img src="' + item.image + '" />'
				: '<div class="sc-no-img"><svg viewBox="0 0 48 48"><rect x="4" y="4" width="40" height="40" rx="8" fill="#F3F4F6" stroke="#D1D5DB" stroke-width="1.5"/><circle cx="17" cy="18" r="4" fill="#D1D5DB"/><path d="M4 34 L14 24 L22 32 L30 22 L44 34" fill="none" stroke="#D1D5DB" stroke-width="1.5" stroke-linejoin="round"/></svg></div>';

			return '<div class="sc-card" data-name="' + item.name.replace(/"/g, '&quot;') + '">'
				+ '<div class="sc-card-img">'
				+   imgHtml
				+   '<div class="sc-card-overlay">'
				+     '<button class="sc-btn-edit" data-name="' + item.name.replace(/"/g, '&quot;') + '" title="Edit">✏️</button>'
				+     '<button class="sc-btn-del" data-name="' + item.name.replace(/"/g, '&quot;') + '" title="Delete">🗑️</button>'
				+   '</div>'
				+ '</div>'
				+ '<div class="sc-card-name">' + item.option_name + '</div>'
				+ '</div>';
		}).join('');
	}

	function bindCardEvents() {
		$('#sc-grid').find('.sc-btn-edit').off('click').on('click', function(e) {
			e.stopPropagation();
			var name = $(this).data('name');
			var item = allItems.find(function(i) { return i.name === name; });
			if (item) open_style_dialog(item, loadItems);
		});

		$('#sc-grid').find('.sc-btn-del').off('click').on('click', function(e) {
			e.stopPropagation();
			var name = $(this).data('name');
			frappe.confirm(
				'Do you want to delete <b>' + name + '</b>?',
				function() {
					frappe.call({
						method: 'frappe.client.delete',
						args: { doctype: 'Style Option', name: name },
						callback: function() {
							frappe.show_alert({ message: 'Deleted', indicator: 'red' });
							loadItems();
						}
					});
				}
			);
		});
	}

	function open_style_dialog(item, onSuccess) {
		var isEdit = !!item;
		var d = new frappe.ui.Dialog({
			title: isEdit ? 'Edit Style — ' + item.option_name : 'Add New Style',
			fields: [
				{
					fieldname: 'option_name',
					fieldtype: 'Data',
					label: 'Style Name',
					reqd: 1,
					read_only: isEdit ? 1 : 0,
					default: isEdit ? item.option_name : ''
				},
				{
					fieldname: 'category',
					fieldtype: 'Select',
					label: 'Category',
					reqd: 1,
					options: '\n' + CATEGORIES.filter(function(c) { return c !== 'All'; }).join('\n'),
					default: isEdit ? item.category : (currentCategory !== 'All' ? currentCategory : '')
				},
				{
					fieldname: 'image',
					fieldtype: 'Attach Image',
					label: 'Image',
					default: isEdit ? item.image : ''
				}
			],
			primary_action_label: isEdit ? 'Update' : 'Add Style',
			primary_action: function(values) {
				if (isEdit) {
					frappe.call({
						method: 'frappe.client.set_value',
						args: {
							doctype: 'Style Option',
							name: item.name,
							fieldname: { category: values.category, image: values.image || '' }
						},
						callback: function() {
							d.hide();
							frappe.show_alert({ message: 'Updated', indicator: 'green' });
							onSuccess();
						}
					});
				} else {
					frappe.call({
						method: 'frappe.client.insert',
						args: {
							doc: {
								doctype: 'Style Option',
								option_name: values.option_name,
								category: values.category,
								image: values.image || ''
							}
						},
						callback: function() {
							d.hide();
							frappe.show_alert({ message: 'Style added!', indicator: 'green' });
							onSuccess();
						}
					});
				}
			}
		});
		d.show();
	}

	loadItems();
};


function inject_catalog_styles() {
	if ($('#sc-styles').length) return;
	$('<style id="sc-styles">'

	+ '* { box-sizing: border-box; }'

	/* ── Page wrap ── */
	+ '.sc-wrap { padding: 0; max-width: 100%; margin: 0; background: #F3F4F6; min-height: 100vh; }'

	/* ── Header — light blue bar ── */
	+ '.sc-header {'
	+   'display: flex; align-items: center; justify-content: space-between;'
	+   'padding: 18px 28px; background: #ADD8E6;'
	+ '}'
	+ '.sc-header-title { font-size: 18px; font-weight: 700; color: #1E3A5F; margin-bottom: 2px; }'
	+ '.sc-header-sub { font-size: 12px; color: #3B6080; }'

	/* ── Add button (white on light blue header) ── */
	+ '.sc-add-btn {'
	+   'padding: 7px 18px; background: #fff;'
	+   'color: #1E3A5F; border: none; border-radius: 6px;'
	+   'font-size: 13px; font-weight: 600; cursor: pointer;'
	+   'white-space: nowrap; flex-shrink: 0; transition: background 0.15s;'
	+   'box-shadow: 0 1px 4px rgba(0,0,0,0.12);'
	+ '}'
	+ '.sc-add-btn:hover { background: #F0F9FF; }'

	/* ── Filter bar ── */
	+ '.sc-filterbar {'
	+   'background: #fff; border-bottom: 1px solid #E5E7EB;'
	+   'padding: 0 28px; display: flex; align-items: center;'
	+   'position: sticky; top: 0; z-index: 10; overflow-x: auto;'
	+ '}'
	+ '.sc-tabs { display: flex; gap: 0; flex: 1; }'
	+ '.sc-tab {'
	+   'padding: 12px 16px; border: none; border-bottom: 3px solid transparent;'
	+   'background: none; font-size: 12.5px; font-weight: 500; color: #6B7280;'
	+   'cursor: pointer; transition: all 0.12s; white-space: nowrap;'
	+ '}'
	+ '.sc-tab:hover { color: #1E3A5F; }'
	+ '.sc-tab.active { color: #1E3A5F; border-bottom-color: #ADD8E6; font-weight: 700; }'

	/* ── Content area ── */
	+ '.sc-content { padding: 24px 28px; min-height: 400px; }'

	/* ── Group ── */
	+ '.sc-group { margin-bottom: 36px; }'
	+ '.sc-group-header {'
	+   'display: flex; align-items: center; gap: 10px; margin-bottom: 14px;'
	+   'padding-bottom: 10px; border-bottom: 1px solid #E5E7EB;'
	+ '}'
	+ '.sc-group-icon { display: none; }'
	+ '.sc-group-title {'
	+   'font-size: 14px; font-weight: 700; color: #111827;'
	+ '}'
	+ '.sc-group-count {'
	+   'background: #D0EAF2; color: #1E3A5F; border-radius: 10px;'
	+   'padding: 1px 8px; font-size: 11px; font-weight: 600;'
	+ '}'
	+ '.sc-group-line { flex: 1; }'

	/* ── Card grid ── */
	+ '.sc-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; }'

	/* ── Card ── */
	+ '.sc-card {'
	+   'border: 1px solid #E5E7EB; border-radius: 10px; overflow: hidden;'
	+   'background: #fff; transition: box-shadow 0.18s, border-color 0.18s; position: relative;'
	+   'display: flex; flex-direction: column; cursor: pointer;'
	+ '}'
	+ '.sc-card:hover { border-color: #93C5FD; box-shadow: 0 4px 16px rgba(28,100,242,0.12); }'

	/* ── Card image ── */
	+ '.sc-card-img {'
	+   'width: 100%; height: 150px; overflow: hidden;'
	+   'background: #F9FAFB;'
	+   'display: flex; align-items: center; justify-content: center; position: relative;'
	+ '}'
	+ '.sc-card-img img { width: 100%; height: 100%; object-fit: cover; display: block; }'
	+ '.sc-no-img { width: 44px; height: 44px; opacity: 0.25; }'
	+ '.sc-no-img svg { width: 100%; height: 100%; }'

	/* ── Hover overlay (edit/delete) ── */
	+ '.sc-card-overlay {'
	+   'position: absolute; top: 6px; right: 6px;'
	+   'display: flex; gap: 4px;'
	+   'opacity: 0; transition: opacity 0.15s;'
	+ '}'
	+ '.sc-card:hover .sc-card-overlay { opacity: 1; }'
	+ '.sc-btn-edit, .sc-btn-del {'
	+   'width: 30px; height: 30px; border: none; border-radius: 6px;'
	+   'cursor: pointer; font-size: 13px;'
	+   'display: flex; align-items: center; justify-content: center;'
	+   'transition: transform 0.1s; padding: 0;'
	+ '}'
	+ '.sc-btn-edit { background: #fff; color: #1E3A5F; box-shadow: 0 1px 4px rgba(0,0,0,0.15); }'
	+ '.sc-btn-edit:hover { background: #EFF6FF; }'
	+ '.sc-btn-del { background: #fff; color: #EF4444; box-shadow: 0 1px 4px rgba(0,0,0,0.15); }'
	+ '.sc-btn-del:hover { background: #FEF2F2; }'

	/* ── Card name ── */
	+ '.sc-card-name {'
	+   'padding: 9px 10px 10px; text-align: center;'
	+   'font-size: 12px; font-weight: 600; color: #374151;'
	+   'background: #fff; border-top: 1px solid #F3F4F6;'
	+   'overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'
	+ '}'

	/* ── Empty state ── */
	+ '.sc-empty { text-align: center; padding: 80px 20px; }'
	+ '.sc-empty-icon { font-size: 48px; margin-bottom: 14px; }'
	+ '.sc-empty-text { font-size: 16px; font-weight: 700; color: #374151; margin-bottom: 6px; }'
	+ '.sc-empty-hint { font-size: 13px; color: #9CA3AF; line-height: 1.8; margin-bottom: 20px; }'
	+ '.sc-empty-btn {'
	+   'display: inline-block; padding: 9px 24px;'
	+   'background: #ADD8E6; color: #1E3A5F; border: none; border-radius: 6px;'
	+   'font-size: 13px; font-weight: 600; cursor: pointer; transition: background 0.15s;'
	+ '}'
	+ '.sc-empty-btn:hover { background: #93CBE0; }'

	+ '</style>').appendTo('head');
}
