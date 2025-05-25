const SUPABASE_URL = 'https://ctcjynoesfdiqkcyyxep.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN0Y2p5bm9lc2ZkaXFrY3l5eGVwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMTMyMzIsImV4cCI6MjA2MzU4OTIzMn0.PTzW2a8rjw_EzW2GK6zyC81jd7cWN2KX7oVRgUVlXyg';

const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

async function uploadFile(fileBlob, type) {
  if (!fileBlob) {
    console.warn("No file provided for upload");
    return null;
  }

  const ext = fileBlob.type?.split("/")?.[1] || (type === "audio" ? "webm" : "jpg");
  const fileName = `${type}-${Date.now()}.${ext}`;
  
  const { data, error } = await supabaseClient.storage
    .from("media") 
    .upload(fileName, fileBlob, {
      contentType: fileBlob.type || (type === "audio" ? "audio/webm" : "image/jpeg"),
      upsert: false,
    });

  if (error) {
    console.error("Upload error:", error.message);
    return null;
  }

  const { data: publicUrlData } = supabaseClient
    .storage
    .from("media")
    .getPublicUrl(fileName);

  return publicUrlData?.publicUrl || null;
}

