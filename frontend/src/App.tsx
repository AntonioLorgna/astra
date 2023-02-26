import { Route, Routes, useLocation } from "react-router-dom";
import './index.css';
import Root from "./routes/Root";



export default function App() {
  let location = useLocation();

  // The `backgroundLocation` state is the location that we were at when one of
  // the gallery links was clicked. If it's there, use it as the location for
  // the <Routes> so we show the gallery in the background, behind the modal.
  let state = location.state as { backgroundLocation?: Location };

  return (
    <>
    <Routes location={state?.backgroundLocation || location}>
      <Route path="/" element={<Root/>}>
      </Route>
    </Routes>
    </>
  );
}
