export default function ClipCard() {
  return (
    <div className="border p-2 rounded shadow">
      <video className="w-full" controls>
        <source src="sample_short.mp4" type="video/mp4" />
      </video>
      <div className="mt-2">
        <p>Emotion: Funny | Score: 82</p>
        <button className="bg-green-500 text-white px-2 py-1 rounded mr-2">Approve</button>
        <button className="bg-red-500 text-white px-2 py-1 rounded">Reject</button>
      </div>
    </div>
  );
}
