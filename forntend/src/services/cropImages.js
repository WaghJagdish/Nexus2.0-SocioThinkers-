const CROP_IMAGES = {
  rice: 'https://images.unsplash.com/photo-1599599810694-b5ac4dd64b4b?auto=format&fit=crop&w=400&h=300&q=80',
  wheat: 'https://images.unsplash.com/photo-1625246333195-78d9c38ad576?auto=format&fit=crop&w=400&h=300&q=80',
  soybean: 'https://images.unsplash.com/photo-1621551247857-f2f8c8975642?auto=format&fit=crop&w=400&h=300&q=80',
  groundnut: 'https://images.unsplash.com/photo-1585518119329-cdf02623cddc?auto=format&fit=crop&w=400&h=300&q=80',
  sugarcane: 'https://images.unsplash.com/photo-1574943320219-553eb213f72d?auto=format&fit=crop&w=400&h=300&q=80',
  cotton: 'https://images.unsplash.com/photo-1635672644657-c426e6e8e57a?auto=format&fit=crop&w=400&h=300&q=80',
  maize: 'https://images.unsplash.com/photo-1585970883917-c6400ca199e7?auto=format&fit=crop&w=400&h=300&q=80',
  mustard: 'https://images.unsplash.com/photo-1611502389593-1feb11e98d11?auto=format&fit=crop&w=400&h=300&q=80',
  chickpea: 'https://images.unsplash.com/photo-1505252585461-04db1267ae5b?auto=format&fit=crop&w=400&h=300&q=80',
  lentil: 'https://images.unsplash.com/photo-1505252585461-04db1267ae5b?auto=format&fit=crop&w=400&h=300&q=80',
  bajra: 'https://images.unsplash.com/photo-1625246333195-78d9c38ad576?auto=format&fit=crop&w=400&h=300&q=80',
  sorghum: 'https://images.unsplash.com/photo-1621551247857-f2f8c8975642?auto=format&fit=crop&w=400&h=300&q=80',
};

const CROP_INFO = {
  rice: { name: 'Rice', emoji: '🍚', season: 'Kharif' },
  wheat: { name: 'Wheat', emoji: '🌾', season: 'Rabi' },
  soybean: { name: 'Soybean', emoji: '🌱', season: 'Kharif' },
  groundnut: { name: 'Groundnut', emoji: '🥜', season: 'Kharif' },
  sugarcane: { name: 'Sugarcane', emoji: '🍃', season: 'Year-round' },
  cotton: { name: 'Cotton', emoji: '☁️', season: 'Kharif' },
  maize: { name: 'Maize', emoji: '🌽', season: 'Kharif' },
  mustard: { name: 'Mustard', emoji: '🌼', season: 'Rabi' },
  chickpea: { name: 'Chickpea', emoji: '🫘', season: 'Rabi' },
  lentil: { name: 'Lentil', emoji: '🫘', season: 'Rabi' },
  bajra: { name: 'Bajra', emoji: '🌾', season: 'Kharif' },
  sorghum: { name: 'Sorghum', emoji: '🌾', season: 'Kharif' },
};

export function getCropImage(cropName) {
  if (!cropName) return CROP_IMAGES.rice;
  const key = cropName.toLowerCase().trim();
  return CROP_IMAGES[key] || CROP_IMAGES.rice;
}

export function getCropInfo(cropName) {
  if (!cropName) return CROP_INFO.rice;
  const key = cropName.toLowerCase().trim();
  return CROP_INFO[key] || { name: cropName, emoji: '🌱', season: 'Unknown' };
}

export function getCropSuitabilityColor(confidence) {
  if (!confidence) return '#4CAF50';
  if (confidence >= 0.8) return '#2e7d32';
  if (confidence >= 0.6) return '#558b2f';
  if (confidence >= 0.4) return '#f57f17';
  return '#d32f2f';
}

export function getCropSuitabilityLabel(confidence) {
  if (!confidence) return 'Not Available';
  if (confidence >= 0.9) return 'Excellent';
  if (confidence >= 0.8) return 'Very Good';
  if (confidence >= 0.7) return 'Good';
  if (confidence >= 0.5) return 'Moderate';
  if (confidence >= 0.3) return 'Fair';
  return 'Poor';
}
