function closeBothModals(lotId, spotId) {
            // Get both modals
            const spotModal = document.getElementById(`spotModal-${lotId}-${spotId}`);
            const parkingModal = document.getElementById(`viewParking-${lotId}`);

            // Use Bootstrap's Modal instance to hide them
            const bsSpotModal = bootstrap.Modal.getInstance(spotModal);
            const bsParkingModal = bootstrap.Modal.getInstance(parkingModal);

            if (bsSpotModal) bsSpotModal.hide();
            if (bsParkingModal) bsParkingModal.hide();

            // Delay the redirect slightly to ensure the modals finish closing
            setTimeout(() => {
                window.location.href = "/admin/dashboard";  // Adjust this to your actual route
            }, 100);
        }