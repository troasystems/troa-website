const sharp = require('sharp');
const path = require('path');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const iconsDir = path.join(__dirname, '../public/icons');
const logoPath = path.join(iconsDir, 'logo-source.jpeg');

async function generateIcons() {
  console.log('Generating PWA icons from logo...');
  
  for (const size of sizes) {
    const outputPath = path.join(iconsDir, `icon-${size}x${size}.png`);
    
    try {
      // Create a square icon with padding and rounded corners
      const padding = Math.floor(size * 0.1); // 10% padding
      const logoSize = size - (padding * 2);
      
      // Resize logo
      const resizedLogo = await sharp(logoPath)
        .resize(logoSize, logoSize, {
          fit: 'contain',
          background: { r: 255, g: 255, b: 255, alpha: 1 }
        })
        .toBuffer();
      
      // Create white background with logo centered
      await sharp({
        create: {
          width: size,
          height: size,
          channels: 4,
          background: { r: 255, g: 255, b: 255, alpha: 1 }
        }
      })
      .composite([{
        input: resizedLogo,
        top: padding,
        left: padding
      }])
      .png()
      .toFile(outputPath);
      
      console.log(`✓ Generated ${size}x${size} icon`);
    } catch (error) {
      console.error(`✗ Failed to generate ${size}x${size} icon:`, error.message);
    }
  }
  
  console.log('\nIcon generation complete!');
}

generateIcons();
