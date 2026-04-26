const CROP_IMAGES = {
  rice: {
    url: 'https://images.unsplash.com/photo-1599599810694-b5ac4dd64b4b?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%238B6F47" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3ERice%3C/text%3E%3C/svg%3E'
  },
  wheat: {
    url: 'https://images.unsplash.com/photo-1625246333195-78d9c38ad576?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23D2B48C" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3EWheat%3C/text%3E%3C/svg%3E'
  },
  soybean: {
    url: 'https://images.unsplash.com/photo-1621551247857-f2f8c8975642?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%236B5D4F" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3ESoybean%3C/text%3E%3C/svg%3E'
  },
  groundnut: {
    url: 'https://images.unsplash.com/photo-1585518119329-cdf02623cddc?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23A0522D" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3EGroundnut%3C/text%3E%3C/svg%3E'
  },
  sugarcane: {
    url: 'https://images.unsplash.com/photo-1574943320219-553eb213f72d?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%234a7c59" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3ESugarcane%3C/text%3E%3C/svg%3E'
  },
  cotton: {
    url: 'https://images.unsplash.com/photo-1635672644657-c426e6e8e57a?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23F5DEB3" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3ECotton%3C/text%3E%3C/svg%3E'
  },
  maize: {
    url: 'https://images.unsplash.com/photo-1585970883917-c6400ca199e7?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23FFD700" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3EMaize%3C/text%3E%3C/svg%3E'
  },
  mustard: {
    url: 'https://images.unsplash.com/photo-1611502389593-1feb11e98d11?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23FFB90F" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3EMustard%3C/text%3E%3C/svg%3E'
  },
  chickpea: {
    url: 'https://images.unsplash.com/photo-1505252585461-04db1267ae5b?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%238B7355" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3EChickpea%3C/text%3E%3C/svg%3E'
  },
  lentil: {
    url: 'https://images.unsplash.com/photo-1505252585461-04db1267ae5b?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23CD853F" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3ELentil%3C/text%3E%3C/svg%3E'
  },
  bajra: {
    url: 'https://images.unsplash.com/photo-1625246333195-78d9c38ad576?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%23DAA520" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3EBajra%3C/text%3E%3C/svg%3E'
  },
  sorghum: {
    url: 'https://images.unsplash.com/photo-1621551247857-f2f8c8975642?auto=format&fit=crop&w=400&h=300&q=80',
    fallback: 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300"%3E%3Crect fill="%238B4513" width="400" height="300"/%3E%3Ctext x="50%25" y="50%25" font-size="48" fill="white" text-anchor="middle" dominant-baseline="middle"%3ESorghum%3C/text%3E%3C/svg%3E'
  },
};

const DB_NAME = 'CropImagesDB';
const DB_STORE = 'images';

let db = null;

const initDB = async () => {
  return new Promise((resolve, reject) => {
    if (db) {
      resolve(db);
      return;
    }

    const request = indexedDB.open(DB_NAME, 1);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      db = request.result;
      resolve(db);
    };

    request.onupgradeneeded = (event) => {
      const store = event.target.result.createObjectStore(DB_STORE);
      store.createIndex('timestamp', 'timestamp', { unique: false });
    };
  });
};

const getCachedImage = async (cropName) => {
  try {
    const database = await initDB();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction([DB_STORE], 'readonly');
      const store = transaction.objectStore(DB_STORE);
      const request = store.get(cropName);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const result = request.result;
        if (result && Date.now() - result.timestamp < 30 * 24 * 60 * 60 * 1000) {
          resolve(result.data);
        } else {
          resolve(null);
        }
      };
    });
  } catch (error) {
    console.warn('Cache retrieval failed:', error);
    return null;
  }
};

const setCachedImage = async (cropName, data) => {
  try {
    const database = await initDB();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction([DB_STORE], 'readwrite');
      const store = transaction.objectStore(DB_STORE);
      const request = store.put(
        {
          name: cropName,
          data: data,
          timestamp: Date.now(),
        },
        cropName
      );

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve();
    });
  } catch (error) {
    console.warn('Cache storage failed:', error);
  }
};

const fetchAndCacheImage = async (cropName) => {
  const imageData = CROP_IMAGES[cropName.toLowerCase()];
  if (!imageData) return CROP_IMAGES.rice.fallback;

  try {
    const cached = await getCachedImage(cropName);
    if (cached) return cached;

    const response = await fetch(imageData.url);
    if (!response.ok) return imageData.fallback;

    const blob = await response.blob();
    const reader = new FileReader();

    return new Promise((resolve) => {
      reader.onload = async (e) => {
        const dataUrl = e.target.result;
        await setCachedImage(cropName, dataUrl);
        resolve(dataUrl);
      };
      reader.onerror = () => resolve(imageData.fallback);
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.warn(`Failed to fetch image for ${cropName}:`, error);
    return imageData.fallback;
  }
};

export async function getCropImage(cropName) {
  if (!cropName) return CROP_IMAGES.rice.fallback;
  const cached = await getCachedImage(cropName);
  if (cached) return cached;
  return fetchAndCacheImage(cropName);
}

export function getCropInfo(cropName) {
  if (!cropName) return { name: 'Unknown', fallback: CROP_IMAGES.rice.fallback };
  const name = cropName.toLowerCase();
  return {
    name: cropName,
    url: CROP_IMAGES[name]?.url,
    fallback: CROP_IMAGES[name]?.fallback || CROP_IMAGES.rice.fallback,
  };
}

export function getCropSuitabilityColor(confidence) {
  if (confidence >= 0.85) return '#4CAF50';
  if (confidence >= 0.70) return '#81C784';
  if (confidence >= 0.50) return '#FFA726';
  return '#EF5350';
}

export function getCropSuitabilityLabel(confidence) {
  if (confidence >= 0.85) return 'Excellent';
  if (confidence >= 0.70) return 'Good';
  if (confidence >= 0.50) return 'Fair';
  return 'Poor';
}

export const preloadAllCropImages = async () => {
  const cropNames = Object.keys(CROP_IMAGES);
  await Promise.all(cropNames.map(crop => fetchAndCacheImage(crop)));
};
