import { useState } from "react";
import { MainButton, useShowPopup } from '@vkruglikov/react-telegram-web-app';



export default function App() {
  const showPopup = useShowPopup();
  

  return (
    <>
      Some page content...
      <MainButton
        text="SHOW POPUP"
        onClick={() => {
          showPopup({
            message: "Hello, I'am showPopup handle",
          });
        }}
      />
    </>
  );
}
