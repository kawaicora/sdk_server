/**
 * VR Utilities for model loading, shader creation, and material management.
 */
const VRUtils = {
    /**
     * Load a model (OBJ or GLTF/GLB depending on extension, FBX not natively supported by a-frame core without extras, 
     * but we can assume GLTF/OBJ for standard a-frame or use a-frame-extras for FBX. 
     * Since the user asked for FBX, we might need a-frame-extras loader or just provide the placeholder structure).
     * For now, we will implement standard A-Frame asset management for models.
     * @param {string} id - ID for the entity
     * @param {string} url - URL of the model file
     * @param {string} type - 'obj', 'gltf', 'fbx' (requires a-frame-extras for fbx)
     * @param {object} position - {x, y, z}
     * @param {object} scale - {x, y, z}
     * @param {object} rotation - {x, y, z}
     * @param {string} parentId - ID of parent entity, defaults to scene
     */
    loadModel: function (id, url, type, position = { x: 0, y: 0, z: 0 }, scale = { x: 1, y: 1, z: 1 }, rotation = { x: 0, y: 0, z: 0 }, parentId = null) {
        const entity = document.createElement('a-entity');
        entity.setAttribute('id', id);
        entity.setAttribute('position', position);
        entity.setAttribute('scale', scale);
        entity.setAttribute('rotation', rotation);

        if (type === 'gltf' || url.endsWith('.gltf') || url.endsWith('.glb')) {
            entity.setAttribute('gltf-model', url);
        } else if (type === 'obj' || url.endsWith('.obj')) {
            entity.setAttribute('obj-model', `obj: url(${url})`);
        } else if (type === 'fbx' || url.endsWith('.fbx')) {
            // Note: Requires a-frame-extras.loaders to be included in HTML
            entity.setAttribute('fbx-model', `src: url(${url})`);
        } else {
            console.warn(`Unknown model type for ${url}`);
        }

        const parent = parentId ? document.getElementById(parentId) : document.querySelector('a-scene');
        if (parent) {
            parent.appendChild(entity);
        } else {
            console.error('Parent entity not found');
        }
        return entity;
    },

    /**
     * Create a standard material with PBR properties.
     * @param {string} id - Material ID (used if creating a mixin, otherwise applied directly)
     * @param {object} props - Material properties
     * @param {string} props.color - Base Color (Hex)
     * @param {number} props.opacity - Opacity (0-1)
     * @param {boolean} props.transparent - Transparent
     * @param {number} props.metalness - Metalness (0-1)
     * @param {number} props.roughness - Roughness (0-1)
     * @param {string} props.emissive - Emissive Color (Hex)
     * @param {number} props.emissiveIntensity - Emissive Intensity
     * @param {string} props.src - Texture map URL
     * @param {string} props.normalMap - Normal map URL
     * @param {string} props.ambientOcclusionMap - AO map URL
     */
    createMaterialConfig: function (props) {
        let materialString = '';
        if (props.color) materialString += `color: ${props.color}; `;
        if (props.opacity !== undefined) materialString += `opacity: ${props.opacity}; `;
        if (props.transparent !== undefined) materialString += `transparent: ${props.transparent}; `;
        if (props.metalness !== undefined) materialString += `metalness: ${props.metalness}; `;
        if (props.roughness !== undefined) materialString += `roughness: ${props.roughness}; `;
        if (props.emissive) materialString += `emissive: ${props.emissive}; `;
        if (props.emissiveIntensity !== undefined) materialString += `emissiveIntensity: ${props.emissiveIntensity}; `;

        // Maps
        if (props.src) materialString += `src: url(${props.src}); `;
        if (props.normalMap) materialString += `normalMap: url(${props.normalMap}); `;
        if (props.ambientOcclusionMap) materialString += `ambientOcclusionMap: url(${props.ambientOcclusionMap}); `;

        return materialString;
    },

    /**
     * Apply material to an entity.
     * @param {string|HTMLElement} entityRef - Entity ID or Element
     * @param {object} materialProps - Properties for createMaterialConfig
     */
    applyMaterial: function (entityRef, materialProps) {
        const entity = typeof entityRef === 'string' ? document.getElementById(entityRef) : entityRef;
        if (!entity) return;

        const matConfig = this.createMaterialConfig(materialProps);
        entity.setAttribute('material', matConfig);
    },

    /**
     * Update the Play Button Style (Example usage of apply material)
     * @param {string} buttonId 
     * @param {boolean} isPlaying 
     */
    updatePlayButtonVisuals: function (buttonId, isPlaying) {
        const btn = document.getElementById(buttonId);
        if (!btn) return;

        if (isPlaying) {
            // Example: Make it glowing red when playing
            this.applyMaterial(btn, {
                color: '#FF0000',
                emissive: '#FF0000',
                emissiveIntensity: 0.5,
                metalness: 0.8,
                roughness: 0.2
            });
        } else {
            // Example: Green when paused (ready to play)
            this.applyMaterial(btn, {
                color: '#00FF00',
                emissive: '#00FF00',
                emissiveIntensity: 0.2,
                metalness: 0.5,
                roughness: 0.5
            });
        }
    }
};

// Global access
window.VRUtils = VRUtils;