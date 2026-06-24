/**
 * TPC-DS Reference Data — Stores and Items
 * Based on the TPC-DS sf1 benchmark dataset from Databricks catalog.
 * Item IDs and store IDs match actual TPC-DS i_item_id / s_store_id format.
 */

export const STORES = [
  { s_store_sk: 1,  s_store_id: 'AAAAAAAABAAAAAAA', s_store_name: 'ought',     s_city: 'Midway',      s_state: 'TN' },
  { s_store_sk: 2,  s_store_id: 'AAAAAAAACAAAAAAA', s_store_name: 'able',       s_city: 'Fairview',    s_state: 'KY' },
  { s_store_sk: 3,  s_store_id: 'AAAAAAAACAAAAAAA', s_store_name: 'pri',        s_city: 'Fairview',    s_state: 'KY' },
  { s_store_sk: 4,  s_store_id: 'AAAAAAAAEAAAAAAA', s_store_name: 'ese',        s_city: 'Midway',      s_state: 'TN' },
  { s_store_sk: 5,  s_store_id: 'AAAAAAAAEAAAAAAA', s_store_name: 'anti',       s_city: 'Spring Hill', s_state: 'TN' },
  { s_store_sk: 6,  s_store_id: 'AAAAAAAAEAAAAAAA', s_store_name: 'cally',      s_city: 'Spring Hill', s_state: 'TN' },
  { s_store_sk: 7,  s_store_id: 'AAAAAAAAHAAAAAAA', s_store_name: 'ation',      s_city: 'Oak Grove',   s_state: 'MN' },
  { s_store_sk: 8,  s_store_id: 'AAAAAAAAIAAAAAAA', s_store_name: 'eing',       s_city: 'Shiloh',      s_state: 'IL' },
  { s_store_sk: 9,  s_store_id: 'AAAAAAAAIAAAAAAA', s_store_name: 'bar',        s_city: 'Shiloh',      s_state: 'IL' },
  { s_store_sk: 10, s_store_id: 'AAAAAAAAKAAAAAAA', s_store_name: 'ought',      s_city: 'Centerville', s_state: 'TX' },
  { s_store_sk: 11, s_store_id: 'AAAAAAAAKAAAAAAA', s_store_name: 'eing',       s_city: 'Centerville', s_state: 'TX' },
  { s_store_sk: 12, s_store_id: 'AAAAAAAAKAAAAAAA', s_store_name: 'able',       s_city: 'Centerville', s_state: 'TX' },
];

export const CATEGORY_ICONS = {
  'Electronics': '💻',
  'Shoes':       '👟',
  'Women':       '👗',
  'Music':       '🎵',
  'Sports':      '⚽',
  'Jewelry':     '💎',
  'Men':         '👔',
  'Home':        '🏠',
  'Books':       '📚',
  'Children':    '🧒',
};

export const CATEGORY_COLORS = {
  'Electronics': '#818cf8',
  'Shoes':       '#f97316',
  'Women':       '#ec4899',
  'Music':       '#10b981',
  'Sports':      '#06b6d4',
  'Jewelry':     '#eab308',
  'Men':         '#8b5cf6',
  'Home':        '#f43f5e',
  'Books':       '#14b8a6',
  'Children':    '#fb923c',
};

export const ITEMS = [
  // ── Electronics ──────────────────────────────────────
  { i_item_sk: 1,  i_item_id: 'AAAAAAAABAAAAAAA', i_category: 'Electronics', i_class: 'scanners',     i_product_name: 'Portable Scanner XR',       i_current_price: 31.87, i_wholesale_cost: 20.70 },
  { i_item_sk: 2,  i_item_id: 'AAAAAAAACAAAAAAA', i_category: 'Electronics', i_class: 'scanners',     i_product_name: 'Flatbed Scanner Pro',        i_current_price: 89.99, i_wholesale_cost: 52.40 },
  { i_item_sk: 3,  i_item_id: 'AAAAAAAACAAAAAAA', i_category: 'Electronics', i_class: 'monitors',     i_product_name: 'Wireless Monitor 27"',       i_current_price: 249.99, i_wholesale_cost: 148.50 },
  { i_item_sk: 4,  i_item_id: 'AAAAAAAAEAAAAAAA', i_category: 'Electronics', i_class: 'monitors',     i_product_name: 'LED Monitor 24" Slim',       i_current_price: 179.99, i_wholesale_cost: 98.70 },
  { i_item_sk: 5,  i_item_id: 'AAAAAAAAEAAAAAAA', i_category: 'Electronics', i_class: 'portable',     i_product_name: 'USB-C Hub Compact',          i_current_price: 14.50, i_wholesale_cost: 6.80 },

  // ── Shoes ────────────────────────────────────────────
  { i_item_sk: 6,  i_item_id: 'AAAAAAAAEAAAAAAA', i_category: 'Shoes', i_class: 'athletic',    i_product_name: 'Running Shoes Elite',         i_current_price: 74.99, i_wholesale_cost: 38.50 },
  { i_item_sk: 7,  i_item_id: 'AAAAAAAAHAAAAAAA', i_category: 'Shoes', i_class: 'athletic',    i_product_name: 'Training Shoes Ultra',        i_current_price: 64.99, i_wholesale_cost: 32.00 },
  { i_item_sk: 8,  i_item_id: 'AAAAAAAAIAAAAAAA', i_category: 'Shoes', i_class: 'casual',      i_product_name: 'Casual Loafers Classic',      i_current_price: 49.99, i_wholesale_cost: 22.50 },
  { i_item_sk: 9,  i_item_id: 'AAAAAAAAIAAAAAAA', i_category: 'Shoes', i_class: 'dress',       i_product_name: 'Oxford Dress Shoes',          i_current_price: 89.99, i_wholesale_cost: 42.00 },
  { i_item_sk: 10, i_item_id: 'AAAAAAAAKAAAAAAA', i_category: 'Shoes', i_class: 'boots',       i_product_name: 'Waterproof Hiking Boots',     i_current_price: 119.99, i_wholesale_cost: 58.00 },

  // ── Women ────────────────────────────────────────────
  { i_item_sk: 11, i_item_id: 'AAAAAAAAKAAAAAAA', i_category: 'Women', i_class: 'dresses',     i_product_name: 'Summer Floral Dress',         i_current_price: 42.39, i_wholesale_cost: 24.94 },
  { i_item_sk: 12, i_item_id: 'AAAAAAAAKAAAAAAA', i_category: 'Women', i_class: 'dresses',     i_product_name: 'Evening Cocktail Dress',      i_current_price: 79.99, i_wholesale_cost: 38.00 },
  { i_item_sk: 13, i_item_id: 'AAAAAAAANAAAAAAA', i_category: 'Women', i_class: 'skirts',      i_product_name: 'Pleated Midi Skirt',          i_current_price: 34.99, i_wholesale_cost: 16.80 },
  { i_item_sk: 14, i_item_id: 'AAAAAAAAOAAAAAAA', i_category: 'Women', i_class: 'blouses',     i_product_name: 'Silk Blouse Elegant',         i_current_price: 54.99, i_wholesale_cost: 28.50 },
  { i_item_sk: 15, i_item_id: 'AAAAAAAAOAAAAAAA', i_category: 'Women', i_class: 'swimwear',    i_product_name: 'Two-Piece Swimsuit',          i_current_price: 38.99, i_wholesale_cost: 18.40 },

  // ── Music ────────────────────────────────────────────
  { i_item_sk: 16, i_item_id: 'AAAAAAAABABAAAAAA', i_category: 'Music', i_class: 'rock',        i_product_name: 'Classic Rock Vinyl LP',       i_current_price: 24.99, i_wholesale_cost: 12.50 },
  { i_item_sk: 17, i_item_id: 'AAAAAAAABABAAAAAA', i_category: 'Music', i_class: 'pop',         i_product_name: 'Pop Hits CD Collection',      i_current_price: 14.99, i_wholesale_cost: 6.80 },
  { i_item_sk: 18, i_item_id: 'AAAAAAAABABAAAAAA', i_category: 'Music', i_class: 'country',     i_product_name: 'Country Gold Album',          i_current_price: 18.99, i_wholesale_cost: 8.50 },
  { i_item_sk: 19, i_item_id: 'AAAAAAAADBAAAAAA', i_category: 'Music', i_class: 'classical',   i_product_name: 'Symphony Orchestra Box Set',  i_current_price: 39.99, i_wholesale_cost: 20.00 },
  { i_item_sk: 20, i_item_id: 'AAAAAAAAEBAAAAAA', i_category: 'Music', i_class: 'jazz',        i_product_name: 'Jazz Masters Vinyl',          i_current_price: 29.99, i_wholesale_cost: 14.50 },

  // ── Sports ───────────────────────────────────────────
  { i_item_sk: 21, i_item_id: 'AAAAAAAAEBAAAAAA', i_category: 'Sports', i_class: 'baseball',   i_product_name: 'Pro Baseball Glove',          i_current_price: 42.39, i_wholesale_cost: 24.94 },
  { i_item_sk: 22, i_item_id: 'AAAAAAAAGBAAAAAA', i_category: 'Sports', i_class: 'baseball',   i_product_name: 'Wooden Baseball Bat',         i_current_price: 34.99, i_wholesale_cost: 18.00 },
  { i_item_sk: 23, i_item_id: 'AAAAAAAAGBAAAAAA', i_category: 'Sports', i_class: 'football',   i_product_name: 'Official Football',           i_current_price: 29.99, i_wholesale_cost: 14.80 },
  { i_item_sk: 24, i_item_id: 'AAAAAAAAGBAAAAAA', i_category: 'Sports', i_class: 'golf',       i_product_name: 'Golf Driver Titanium',        i_current_price: 149.99, i_wholesale_cost: 72.00 },
  { i_item_sk: 25, i_item_id: 'AAAAAAAAJBAAAAAA', i_category: 'Sports', i_class: 'fitness',    i_product_name: 'Resistance Bands Set',        i_current_price: 19.99, i_wholesale_cost: 8.50 },

  // ── Jewelry ──────────────────────────────────────────
  { i_item_sk: 26, i_item_id: 'AAAAAAAAKBAAAAAA', i_category: 'Jewelry', i_class: 'rings',       i_product_name: 'Sterling Silver Ring',       i_current_price: 59.99, i_wholesale_cost: 28.00 },
  { i_item_sk: 27, i_item_id: 'AAAAAAAAKBAAAAAA', i_category: 'Jewelry', i_class: 'necklaces',   i_product_name: 'Gold Pendant Necklace',      i_current_price: 89.99, i_wholesale_cost: 42.00 },
  { i_item_sk: 28, i_item_id: 'AAAAAAAAMBAAAAAA', i_category: 'Jewelry', i_class: 'bracelets',   i_product_name: 'Charm Bracelet Set',         i_current_price: 34.99, i_wholesale_cost: 16.00 },
  { i_item_sk: 29, i_item_id: 'AAAAAAAAMBAAAAAA', i_category: 'Jewelry', i_class: 'earrings',    i_product_name: 'Crystal Drop Earrings',      i_current_price: 44.99, i_wholesale_cost: 20.00 },
  { i_item_sk: 30, i_item_id: 'AAAAAAAAMBAAAAAA', i_category: 'Jewelry', i_class: 'watches',     i_product_name: 'Analog Dress Watch',         i_current_price: 129.99, i_wholesale_cost: 62.00 },

  // ── Men ──────────────────────────────────────────────
  { i_item_sk: 31, i_item_id: 'AAAAAAAAPBAAAAAA', i_category: 'Men', i_class: 'shirts',      i_product_name: 'Slim Fit Dress Shirt',        i_current_price: 39.99, i_wholesale_cost: 18.50 },
  { i_item_sk: 32, i_item_id: 'AAAAAAAACAAAAAAA', i_category: 'Men', i_class: 'shirts',      i_product_name: 'Casual Polo Shirt',           i_current_price: 29.99, i_wholesale_cost: 14.00 },
  { i_item_sk: 33, i_item_id: 'AAAAAAAACAAAAAAA', i_category: 'Men', i_class: 'pants',       i_product_name: 'Chino Pants Classic',         i_current_price: 44.99, i_wholesale_cost: 22.00 },
  { i_item_sk: 34, i_item_id: 'AAAAAAAACCAAAAAA', i_category: 'Men', i_class: 'suits',       i_product_name: 'Two-Piece Business Suit',     i_current_price: 199.99, i_wholesale_cost: 95.00 },
  { i_item_sk: 35, i_item_id: 'AAAAAAAACCAAAAAA', i_category: 'Men', i_class: 'accessories', i_product_name: 'Leather Belt Premium',        i_current_price: 24.99, i_wholesale_cost: 10.50 },

  // ── Home ─────────────────────────────────────────────
  { i_item_sk: 36, i_item_id: 'AAAAAAAACCAAAAAA', i_category: 'Home', i_class: 'kitchen',    i_product_name: 'Stainless Steel Pan Set',     i_current_price: 69.99, i_wholesale_cost: 34.00 },
  { i_item_sk: 37, i_item_id: 'AAAAAAAAFCAAAAAA', i_category: 'Home', i_class: 'kitchen',    i_product_name: 'Chef Knife Block',            i_current_price: 49.99, i_wholesale_cost: 24.00 },
  { i_item_sk: 38, i_item_id: 'AAAAAAAAGCAAAAAA', i_category: 'Home', i_class: 'bedding',    i_product_name: 'Cotton Sheet Set Queen',      i_current_price: 54.99, i_wholesale_cost: 26.00 },
  { i_item_sk: 39, i_item_id: 'AAAAAAAAGCAAAAAA', i_category: 'Home', i_class: 'furniture',  i_product_name: 'Accent Side Table',           i_current_price: 89.99, i_wholesale_cost: 42.00 },
  { i_item_sk: 40, i_item_id: 'AAAAAAAAICAAAAAA', i_category: 'Home', i_class: 'decor',      i_product_name: 'Ceramic Vase Modern',         i_current_price: 29.99, i_wholesale_cost: 12.00 },

  // ── Books ────────────────────────────────────────────
  { i_item_sk: 41, i_item_id: 'AAAAAAAAICAAAAAA', i_category: 'Books', i_class: 'fiction',     i_product_name: 'Mystery Thriller Novel',     i_current_price: 16.99, i_wholesale_cost: 7.50 },
  { i_item_sk: 42, i_item_id: 'AAAAAAAAICAAAAAA', i_category: 'Books', i_class: 'fiction',     i_product_name: 'Sci-Fi Adventure Epic',      i_current_price: 14.99, i_wholesale_cost: 6.80 },
  { i_item_sk: 43, i_item_id: 'AAAAAAAALCAAAAAA', i_category: 'Books', i_class: 'history',    i_product_name: 'World History Compendium',   i_current_price: 24.99, i_wholesale_cost: 12.00 },
  { i_item_sk: 44, i_item_id: 'AAAAAAAAMCAAAAAA', i_category: 'Books', i_class: 'self-help',  i_product_name: 'Mindfulness Guide',          i_current_price: 12.99, i_wholesale_cost: 5.50 },
  { i_item_sk: 45, i_item_id: 'AAAAAAAAMCAAAAAA', i_category: 'Books', i_class: 'cooking',    i_product_name: 'Mediterranean Cookbook',      i_current_price: 19.99, i_wholesale_cost: 9.00 },

  // ── Children ─────────────────────────────────────────
  { i_item_sk: 46, i_item_id: 'AAAAAAAAOCAAAAAA', i_category: 'Children', i_class: 'toddler',    i_product_name: 'Building Blocks Set',      i_current_price: 22.99, i_wholesale_cost: 10.00 },
  { i_item_sk: 47, i_item_id: 'AAAAAAAAOCAAAAAA', i_category: 'Children', i_class: 'newborn',    i_product_name: 'Baby Onesie Pack (3)',      i_current_price: 18.99, i_wholesale_cost: 8.50 },
  { i_item_sk: 48, i_item_id: 'AAAAAAAAOCAAAAAA', i_category: 'Children', i_class: 'school-age', i_product_name: 'Kids Backpack Colorful',    i_current_price: 29.99, i_wholesale_cost: 14.00 },
  { i_item_sk: 49, i_item_id: 'AAAAAAAABDAAAAAA', i_category: 'Children', i_class: 'toddler',    i_product_name: 'Plush Teddy Bear',          i_current_price: 15.99, i_wholesale_cost: 6.50 },
  { i_item_sk: 50, i_item_id: 'AAAAAAAACDAAAAAA', i_category: 'Children', i_class: 'infant',     i_product_name: 'Baby Monitor Smart',        i_current_price: 59.99, i_wholesale_cost: 28.00 },
];

/**
 * Group items by category for display.
 * Returns: [{ category, icon, color, items: [...] }, ...]
 */
export function getItemsByCategory() {
  const categoryMap = {};

  for (const item of ITEMS) {
    if (!categoryMap[item.i_category]) {
      categoryMap[item.i_category] = {
        category: item.i_category,
        icon: CATEGORY_ICONS[item.i_category] || '📦',
        color: CATEGORY_COLORS[item.i_category] || '#6b7280',
        items: [],
      };
    }
    categoryMap[item.i_category].items.push(item);
  }

  const ORDER = ['Electronics', 'Shoes', 'Women', 'Music', 'Sports', 'Jewelry', 'Men', 'Home', 'Books', 'Children'];
  return ORDER.map((cat) => categoryMap[cat]).filter(Boolean);
}
