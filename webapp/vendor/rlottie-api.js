import Module from "./rlottie.js";
let api;
let promise;
export function init(url) {
    if (api) {
        return api;
    }
    if (promise) {
        return promise;
    }
    return promise = (async () => {
        const module_ = await Module(url ? { locateFile: () => url } : {});
        api = {
            lottie_init: module_.cwrap("lottie_init", "number", []),
            lottie_destroy: module_.cwrap("lottie_destroy", null, ["number"]),
            lottie_resize: module_.cwrap("lottie_resize", null, [
                "number",
                "number",
                "number",
            ]),
            lottie_buffer: module_.cwrap("lottie_buffer", "number", ["number"]),
            lottie_render: module_.cwrap("lottie_render", null, ["number", "number"]),
            lottie_load_from_data: module_.cwrap("lottie_load_from_data", "number", [
                "number",
                "number",
            ]),
            get HEAPU8() { return module_.HEAPU8; },  // при росте памяти wasm буфер пересоздаётся
            _malloc: module_._malloc,
        };
        return api;
    })().finally(() => promise = undefined);
}
